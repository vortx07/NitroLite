"""
NitroLite Backend Hardware Controller
Direct low-level communication with Acer Nitro Service without Electron bloat.
Author: Built with Antigravity for Acer Nitro Laptops
"""

import socket
import json
import struct
import datetime
import hashlib
import hmac
import base64
import winreg
import threading
import time
from typing import Optional, Dict, Any


class OperatingMode:
    QUIET = 0
    BALANCED = 1
    GAMING = 4
    ECO = 6

    LABELS = {
        QUIET: "Quiet",
        BALANCED: "Balanced",
        GAMING: "Gaming / Extreme",
        ECO: "Eco"
    }


class FanMode:
    AUTO = 0
    MAX = 1
    CUSTOM = 2

    LABELS = {
        AUTO: "Auto",
        MAX: "Max (100%)",
        CUSTOM: "Custom"
    }


class PacketID:
    INITIALIZATION = 0
    GET_MONITOR_DATA = 10
    GET_UPDATED_DATA = 20
    GET_CONNECTED_DEVICE = 30
    GET_LIGHTING_EFFECT_CAPABILITY = 40
    SET_DEVICE_DATA = 100


def get_system_product_name() -> str:
    """Read Acer SystemProductName from Windows Registry."""
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\BIOS")
        val, _ = winreg.QueryValueEx(key, "SystemProductName")
        winreg.CloseKey(key)
        return str(val).strip()
    except Exception:
        return "Nitro ANV15-52"


def _invert_case(s: str) -> str:
    return "".join(c.upper() if c.islower() else c.lower() for c in s)


def _generate_challenge_key(model_name: str, dt: datetime.datetime) -> str:
    r = (dt.hour + 21) * dt.day
    n = _invert_case(model_name)
    o = base64.b64encode(n.encode("utf-8")).decode("utf-8") + str(r)
    s = base64.b64encode(o.encode("utf-8")).decode("utf-8")
    a = hashlib.sha256(s.encode("utf-8")).hexdigest()
    return a[7:22] + a[-3:][::-1]


def _b64url(s: Any) -> str:
    if isinstance(s, str):
        s = s.encode("utf-8")
    return base64.b64encode(s).decode("utf-8").replace("+", "-").replace("/", "_").replace("=", "")


def _build_jwt(payload: Dict[str, Any], key: str) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    h_b64 = _b64url(json.dumps(header, separators=(",", ":")))
    p_b64 = _b64url(json.dumps(payload, separators=(",", ":")))
    msg = f"{h_b64}.{p_b64}".encode("utf-8")
    sig = hmac.new(key.encode("utf-8"), msg, hashlib.sha256).digest()
    sig_b64 = _b64url(sig)
    return f"{h_b64}.{p_b64}.{sig_b64}"


class AcerNitroController:
    """Thread-safe controller for Acer Nitro hardware features."""

    def __init__(self, host: str = "127.0.0.1", port: int = 46933):
        self.host = host
        self.port = port
        self.model_name = get_system_product_name()
        self.sock: Optional[socket.socket] = None
        self.lock = threading.Lock()
        self.connected = False
        
        # Cached device specs
        self.cpu_name = "Intel Core Processor"
        self.gpu_name = "NVIDIA Dedicated GPU"
        self.supported_modes = [OperatingMode.QUIET, OperatingMode.BALANCED, OperatingMode.GAMING, OperatingMode.ECO]

    def connect(self) -> bool:
        """Establish connection with AcerAgentService and complete authentication."""
        with self.lock:
            return self._connect_locked()

    def _connect_locked(self) -> bool:
        if self.sock:
            try:
                self.sock.close()
            except Exception:
                pass
            self.sock = None
        self.connected = False

        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(3.0)
            s.connect((self.host, self.port))
            
            # 1. Request Challenge
            now = datetime.datetime.now()
            self._send_packet_locked(s, PacketID.INITIALIZATION, {"Function": "Request_Challenge"})
            res = self._recv_json_locked(s, timeout=2.0)
            if not res or res.get("result") != "0":
                s.close()
                return False

            nonce = res.get("Nonce")
            expire = res.get("Expire", 60)
            iat = int(now.timestamp())
            key = _generate_challenge_key(self.model_name, now)
            token = _build_jwt({"iat": iat, "exp": iat + expire, "nonce": nonce}, key)

            # 2. Complete Challenge
            self._send_packet_locked(s, PacketID.INITIALIZATION, {"Function": "Challenge", "Nonce": nonce, "Token": token})
            auth_res = self._recv_json_locked(s, timeout=2.0)
            if not auth_res or auth_res.get("result") != "0":
                s.close()
                return False

            self.sock = s
            self.connected = True
            
            # Fetch Hardware Names (best effort)
            try:
                self._send_packet_locked(s, PacketID.INITIALIZATION, {"Function": "SUPPORT_CPU_INFO"})
                c_res = self._recv_json_locked(s, timeout=1.0)
                if c_res and isinstance(c_res.get("data"), list) and len(c_res["data"]) > 0:
                    self.cpu_name = c_res["data"][0].get("cpu_name", self.cpu_name)

                self._send_packet_locked(s, PacketID.INITIALIZATION, {"Function": "SUPPORT_GPU_INFO"})
                g_res = self._recv_json_locked(s, timeout=1.0)
                if g_res and isinstance(g_res.get("data"), list) and len(g_res["data"]) > 0:
                    self.gpu_name = g_res["data"][0].get("gpu_name", self.gpu_name)
            except Exception:
                pass

            return True
        except Exception:
            self.connected = False
            return False

    def _send_packet_locked(self, s: socket.socket, packet_id: int, payload: Dict[str, Any]):
        body = json.dumps(payload).encode("utf-8")
        header = b"ACER" + struct.pack("<I", packet_id)
        s.sendall(header + body)

    def _recv_json_locked(self, s: socket.socket, timeout: float = 2.0) -> Optional[Dict[str, Any]]:
        s.settimeout(timeout)
        buf = ""
        bracket_count = 0
        in_str = False
        escape = False
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                chunk = s.recv(4096)
                if not chunk:
                    break
                text = chunk.decode("utf-8", errors="ignore")
                for c in text:
                    if c == '"' and not escape:
                        in_str = not in_str
                    if not in_str:
                        if c == "{":
                            bracket_count += 1
                        elif c == "}":
                            bracket_count -= 1
                    if bracket_count > 0 or c == "}":
                        buf += c
                    if bracket_count == 0 and buf.strip().startswith("{") and buf.strip().endswith("}"):
                        try:
                            return json.loads(buf)
                        except Exception:
                            buf = ""
                    escape = (c == "\\" and not escape)
            except socket.timeout:
                break
            except Exception:
                break
        return None

    def _ensure_connected_locked(self) -> bool:
        if self.connected and self.sock:
            return True
        return self._connect_locked()

    def get_monitoring_data(self) -> Optional[Dict[str, Any]]:
        """Fetch real-time CPU/GPU temperatures, fan RPM, frequencies, and usage."""
        with self.lock:
            if not self._ensure_connected_locked():
                return None
            try:
                self._send_packet_locked(self.sock, PacketID.GET_MONITOR_DATA, {})
                res = self._recv_json_locked(self.sock, timeout=1.5)
                if res and res.get("result") == "0":
                    return res.get("data", {})
                return None
            except Exception:
                self.connected = False
                return None

    def get_operating_mode(self) -> Optional[int]:
        """Get currently active performance mode (0=Quiet, 1=Balanced, 4=Gaming, 6=Eco)."""
        with self.lock:
            if not self._ensure_connected_locked():
                return None
            try:
                self._send_packet_locked(self.sock, PacketID.GET_UPDATED_DATA, {"Function": "OPERATING_MODE"})
                res = self._recv_json_locked(self.sock, timeout=1.5)
                if res and res.get("result") == "0":
                    return res.get("data", {}).get("mode")
                return None
            except Exception:
                self.connected = False
                return None

    def set_operating_mode(self, mode: int) -> bool:
        """Set performance profile (0=Quiet, 1=Balanced, 4=Gaming, 6=Eco)."""
        with self.lock:
            if not self._ensure_connected_locked():
                return False
            try:
                self._send_packet_locked(
                    self.sock,
                    PacketID.SET_DEVICE_DATA,
                    {"Function": "OPERATING_MODE", "Parameter": {"mode": mode}}
                )
                res = self._recv_json_locked(self.sock, timeout=1.5)
                return bool(res and res.get("result") == "0")
            except Exception:
                self.connected = False
                return False

    def set_fan_control(self, mode: int, cpu_speed: Optional[int] = None, gpu_speed: Optional[int] = None) -> bool:
        """
        Set fan control.
        mode: 0 = Auto, 1 = Max (100%), 2 = Custom
        cpu_speed: 0..100% (if custom)
        gpu_speed: 0..100% (if custom)
        """
        with self.lock:
            if not self._ensure_connected_locked():
                return False
            try:
                param = {
                    "mode": mode,
                    "custom_fan_data": [
                        {
                            "fan_custom_auto": 1 if cpu_speed is None else 0,
                            "fan_custom_speed": 30 if cpu_speed is None else int(cpu_speed),
                            "fan_index": 0,
                            "fan_name": "CPU"
                        },
                        {
                            "fan_custom_auto": 1 if gpu_speed is None else 0,
                            "fan_custom_speed": 30 if gpu_speed is None else int(gpu_speed),
                            "fan_index": 0,
                            "fan_name": "GPU"
                        }
                    ]
                }
                self._send_packet_locked(
                    self.sock,
                    PacketID.SET_DEVICE_DATA,
                    {"Function": "FAN_CONTROL", "Parameter": param}
                )
                res = self._recv_json_locked(self.sock, timeout=1.5)
                return bool(res and res.get("result") == "0")
            except Exception:
                self.connected = False
                return False

    def get_toggle_status(self, feature_name: str) -> Optional[int]:
        """Query state of LCD_OVERDRIVE, WIN_KEY, BACKLIGHT_30S, or BATTERY_BOOST."""
        with self.lock:
            if not self._ensure_connected_locked():
                return None
            try:
                self._send_packet_locked(self.sock, PacketID.GET_UPDATED_DATA, {"Function": feature_name})
                res = self._recv_json_locked(self.sock, timeout=1.5)
                if res and res.get("result") == "0":
                    return res.get("data", {}).get("status")
                return None
            except Exception:
                self.connected = False
                return None

    def set_toggle_status(self, feature_name: str, status: int) -> bool:
        """Enable (1) or Disable (0) a toggle (WIN_KEY, LCD_OVERDRIVE, etc.)."""
        with self.lock:
            if not self._ensure_connected_locked():
                return False
            try:
                self._send_packet_locked(
                    self.sock,
                    PacketID.SET_DEVICE_DATA,
                    {"Function": feature_name, "Parameter": {"status": int(status)}}
                )
                res = self._recv_json_locked(self.sock, timeout=1.5)
                return bool(res and res.get("result") == "0")
            except Exception:
                self.connected = False
                return False

    def close(self):
        """Close socket gracefully."""
        with self.lock:
            if self.sock:
                try:
                    self.sock.close()
                except Exception:
                    pass
                self.sock = None
            self.connected = False
