"""
DualCam Studio - OBS replacement for Zoom (Windows)
====================================================
Studio: 2 cameras + microphone, scenes, audio meter, program output.
Output: its OWN virtual camera (Unity Video Capture driver - NO OBS needed).
In the Zoom app: Settings > Video > Camera > "Unity Video Capture"
                 Settings > Audio > Microphone > your microphone
One-time only: run Setup_Virtual_Camera.bat once (registers the free
UnityCapture driver, MIT licence). The Studio itself needs no admin.
"""
import sys, time
from datetime import datetime

try:
    import cv2
    import numpy as np
except ImportError:
    print("Missing OpenCV: pip install opencv-python numpy Pillow pyvirtualcam")
    sys.exit(1)
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

try:
    import pyvirtualcam
    HAS_VCAM_LIB = True
except Exception:
    HAS_VCAM_LIB = False

try:
    import sounddevice as sd
    HAS_SD = True
except Exception:
    HAS_SD = False

BACKEND = cv2.CAP_DSHOW if sys.platform.startswith("win") else cv2.CAP_ANY
BG, PANEL, PANEL2, TXT, MUT, ACC, RED, GRN = "#0b0d10", "#14171c", "#20242b", "#e8eaed", "#9aa3ad", "#3ea6ff", "#e33", "#0a7d4f"
OUT = {"720p  1280 x 720": (1280, 720), "1080p 1920 x 1080": (1920, 1080), "480p  854 x 480": (854, 480)}


def detect_cameras(maxi=10):
    found = []
    for i in range(maxi):
        cap = cv2.VideoCapture(i, BACKEND)
        if cap.isOpened():
            ok, _ = cap.read()
            if ok:
                found.append(i)
        cap.release()
    return found


def fit(frame, w, h):
    if frame is None:
        img = np.zeros((h, w, 3), dtype=np.uint8)
        cv2.putText(img, "No signal", (24, h // 2), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (170, 170, 170), 2, cv2.LINE_AA)
        return img
    fh, fw = frame.shape[:2]
    s = max(w / fw, h / fh)
    nf = cv2.resize(frame, (int(fw * s) + 1, int(fh * s) + 1))
    y, x = (nf.shape[0] - h) // 2, (nf.shape[1] - w) // 2
    return nf[y:y + h, x:x + w]


def label(img, text):
    if text:
        cv2.rectangle(img, (0, img.shape[0] - 34), (170, img.shape[0]), (0, 0, 0), -1)
        cv2.putText(img, text, (10, img.shape[0] - 11), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)
    return img


class Studio(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("DualCam Studio - OBS Replacement for Zoom")
        self.geometry("1240x760")
        self.configure(bg=BG)
        self.caps, self.running, self.streaming = {}, False, False
        self.vcam, self.vcam_ctx = None, None
        self.scene = tk.StringVar(value="side")
        self.found, self.last_frame = [], None
        self.mic_level, self.mic_stream = 0.0, None
        self.writer, self.rec_start = None, None
        self.fps_t, self.fps_n = time.time(), 0
        self._style()
        self._ui()
        self.refresh()
        self.protocol("WM_DELETE_WINDOW", self.close)

    def _style(self):
        st = ttk.Style(self)
        st.theme_use("clam")
        st.configure("TFrame", background=BG)
        st.configure("Panel.TFrame", background=PANEL)
        st.configure("TLabel", background=BG, foreground=TXT, font=("Segoe UI", 10))
        st.configure("Panel.TLabel", background=PANEL, foreground=TXT, font=("Segoe UI", 10))
        st.configure("Head.TLabel", background=PANEL, foreground=MUT, font=("Segoe UI", 9, "bold"))
        st.configure("TButton", background=PANEL2, foreground=TXT, font=("Segoe UI", 10, "bold"), padding=7)
        st.configure("Go.TButton", background=GRN, foreground="white", font=("Segoe UI", 11, "bold"), padding=9)
        st.configure("Live.TButton", background="#b02020", foreground="white", font=("Segoe UI", 11, "bold"), padding=9)

    def _ui(self):
        top = tk.Frame(self, bg=PANEL, height=52)
        top.pack(fill="x")
        tk.Label(top, text="DualCam  STUDIO", bg=PANEL, fg=TXT, font=("Segoe UI", 16, "bold")).pack(side="left", padx=14, pady=8)
        tk.Label(top, text="OBS replacement - 2 cameras + mic - own virtual camera to Zoom", bg=PANEL, fg=MUT, font=("Segoe UI", 10)).pack(side="left")
        self.live_lbl = tk.Label(top, text="  STANDBY  ", bg=PANEL2, fg=TXT, font=("Segoe UI", 11, "bold"))
        self.live_lbl.pack(side="right", padx=14)
        self.fps_lbl = tk.Label(top, text="", bg=PANEL, fg=MUT, font=("Segoe UI", 10))
        self.fps_lbl.pack(side="right")

        body = ttk.Frame(self)
        body.pack(fill="both", expand=True, padx=8, pady=8)

        left = ttk.Frame(body, style="Panel.TFrame", width=210)
        left.pack(side="left", fill="y", padx=(0, 8))
        ttk.Label(left, text="SCENES", style="Head.TLabel").pack(anchor="w", padx=10, pady=(10, 4))
        for key, name, sub in [("side", "Side by Side", "Cam 1 left - Cam 2 right"), ("pip", "Picture in Picture", "Cam 2 bottom right"),
                               ("top", "Top / Bottom", ""), ("cam1", "Cam 1 Solo", ""), ("cam2", "Cam 2 Solo", "")]:
            ttk.Radiobutton(left, text=name, value=key, variable=self.scene).pack(anchor="w", padx=12, pady=2)
        ttk.Label(left, text="OUTPUT SIZE", style="Head.TLabel").pack(anchor="w", padx=10, pady=(14, 4))
        self.outsize = ttk.Combobox(left, state="readonly", values=list(OUT), width=20)
        self.outsize.set("720p  1280 x 720")
        self.outsize.pack(padx=10)
        ttk.Label(left, text="In Zoom app select camera:\nUnity Video Capture", style="Panel.TLabel").pack(anchor="w", padx=10, pady=14)

        centre = ttk.Frame(body)
        centre.pack(side="left", fill="both", expand=True)
        self.preview = tk.Label(centre, bg="black")
        self.preview.pack(fill="both", expand=True)
        bar = ttk.Frame(centre)
        bar.pack(fill="x", pady=8)
        self.btn_start = ttk.Button(bar, text="START STUDIO", style="Go.TButton", command=self.toggle_run)
        self.btn_start.pack(side="left")
        self.btn_live = ttk.Button(bar, text="GO LIVE TO ZOOM", style="Live.TButton", command=self.toggle_live)
        self.btn_live.pack(side="left", padx=8)
        ttk.Button(bar, text="Record", command=self.toggle_rec).pack(side="left")
        ttk.Button(bar, text="Snapshot", command=self.snapshot).pack(side="left", padx=6)
        self.status = ttk.Label(bar, text="Detecting...")
        self.status.pack(side="left", padx=10)

        right = ttk.Frame(body, style="Panel.TFrame", width=280)
        right.pack(side="left", fill="y", padx=(8, 0))
        ttk.Label(right, text="SOURCES", style="Head.TLabel").pack(anchor="w", padx=10, pady=(10, 4))
        ttk.Label(right, text="Camera 1 (webcam)", style="Panel.TLabel").pack(anchor="w", padx=10)
        self.cam1 = ttk.Combobox(right, state="readonly", width=30)
        self.cam1.pack(padx=10, pady=(0, 6))
        ttk.Label(right, text="Camera 2 (wired / USB)", style="Panel.TLabel").pack(anchor="w", padx=10)
        self.cam2 = ttk.Combobox(right, state="readonly", width=30)
        self.cam2.pack(padx=10, pady=(0, 6))
        ttk.Button(right, text="Detect Devices", command=self.refresh).pack(padx=10, anchor="w")
        ttk.Button(right, text="Swap Cameras", command=self.swap).pack(padx=10, pady=6, anchor="w")
        self.mirror = tk.BooleanVar(value=True)
        ttk.Checkbutton(right, text="Mirror Camera 1", variable=self.mirror).pack(anchor="w", padx=10)
        self.labels = tk.BooleanVar(value=True)
        ttk.Checkbutton(right, text="Show labels", variable=self.labels).pack(anchor="w", padx=10)
        ttk.Label(right, text="AUDIO MIXER - MICROPHONE", style="Head.TLabel").pack(anchor="w", padx=10, pady=(16, 4))
        ttk.Label(right, text="Microphone", style="Panel.TLabel").pack(anchor="w", padx=10)
        self.mic = ttk.Combobox(right, state="readonly", width=30)
        self.mic.pack(padx=10, pady=(0, 6))
        self.meter = tk.Canvas(right, width=250, height=16, bg="#0a0c0e", highlightthickness=1, highlightbackground="#333")
        self.meter.pack(padx=10)
        self.meter_bar = self.meter.create_rectangle(0, 0, 0, 16, fill="#2ecc71", outline="")
        ttk.Label(right, text="Zoom audio: select this same\nmicrophone in the Zoom app.", style="Panel.TLabel").pack(anchor="w", padx=10, pady=10)
        ttk.Label(right, text="VIRTUAL CAMERA", style="Head.TLabel").pack(anchor="w", padx=10, pady=(10, 4))
        self.vcam_lbl = ttk.Label(right, text="Not streaming", style="Panel.TLabel", wraplength=250)
        self.vcam_lbl.pack(anchor="w", padx=10)

    # ---------- devices ----------
    def refresh(self):
        self.status.config(text="Detecting cameras and microphones...")
        self.update_idletasks()
        self.found = detect_cameras()
        names = [f"Camera {i}" for i in self.found]
        self.cam1["values"] = names
        self.cam2["values"] = names
        if names:
            self.cam1.current(0)
        if len(names) > 1:
            self.cam2.current(1)
        elif names:
            self.cam2.current(0)
        mics = []
        if HAS_SD:
            try:
                for i, d in enumerate(sd.query_devices()):
                    if d["max_input_channels"] > 0:
                        mics.append((i, d["name"]))
            except Exception:
                pass
        self.mic_list = mics
        self.mic["values"] = [n for _, n in mics] or ["(default microphone)"]
        if self.mic["values"]:
            self.mic.current(0)
        self.status.config(text=f"Found {len(names)} camera(s), {len(mics)} microphone(s). Press START STUDIO.")
        self._start_mic_meter()

    def _start_mic_meter(self):
        if not HAS_SD or not getattr(self, "mic_list", None):
            return
        try:
            if self.mic_stream:
                self.mic_stream.close()
            dev = self.mic_list[self.mic.current()][0] if self.mic.current() >= 0 else None

            def cb(indata, frames, t, status):
                self.mic_level = float(np.sqrt(np.mean(indata ** 2))) if len(indata) else 0.0

            self.mic_stream = sd.InputStream(device=dev, channels=1, callback=cb)
            self.mic_stream.start()
            self.mic.bind("<<ComboboxSelected>>", lambda e: self._start_mic_meter())
        except Exception:
            pass

    def swap(self):
        a, b = self.cam1.current(), self.cam2.current()
        if a >= 0 and b >= 0:
            self.cam1.current(b)
            self.cam2.current(a)

    def _cap(self, idx):
        if idx not in self.caps:
            c = cv2.VideoCapture(idx, BACKEND)
            c.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            c.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            self.caps[idx] = c
        return self.caps[idx]

    def _read(self, idx, mirror=False):
        ok, f = self._cap(idx).read()
        if not ok:
            return None
        return cv2.flip(f, 1) if mirror else f

    def mix(self, f1, f2, W, H):
        lab = self.labels.get()
        s = self.scene.get()
        if s == "cam1":
            return label(fit(f1, W, H), "Camera 1" if lab else "")
        if s == "cam2":
            return label(fit(f2, W, H), "Camera 2" if lab else "")
        if s == "top":
            return np.vstack([label(fit(f1, W, H // 2), "Camera 1" if lab else ""), label(fit(f2, W, H - H // 2), "Camera 2" if lab else "")])
        if s == "pip":
            base = label(fit(f1, W, H), "Camera 1" if lab else "")
            pw, ph = W // 3, H // 3
            small = fit(f2, pw, ph)
            cv2.rectangle(small, (0, 0), (pw - 1, ph - 1), (255, 255, 255), 3)
            base[H - ph - 16:H - 16, W - pw - 16:W - 16] = small
            return base
        return np.hstack([label(fit(f1, W // 2, H), "Camera 1" if lab else ""), label(fit(f2, W - W // 2, H), "Camera 2" if lab else "")])

    # ---------- run / live ----------
    def toggle_run(self):
        if self.running:
            self.running = False
            if self.streaming:
                self.toggle_live()
            for c in self.caps.values():
                c.release()
            self.caps.clear()
            self.btn_start.config(text="START STUDIO")
            self.live_lbl.config(text="  STANDBY  ", bg=PANEL2)
            self.status.config(text="Stopped.")
            return
        if not self.found:
            messagebox.showwarning("No camera", "No camera found. Plug in both cameras and press Detect Devices.")
            return
        self.running = True
        self.btn_start.config(text="STOP STUDIO")
        self.live_lbl.config(text="  STUDIO ON  ", bg=GRN)
        self.status.config(text="Studio running. Press GO LIVE TO ZOOM to send it as a camera to the Zoom app.")
        self.loop()

    def toggle_live(self):
        if self.streaming:
            self.streaming = False
            try:
                self.vcam_ctx.__exit__(None, None, None)
            except Exception:
                pass
            self.vcam = self.vcam_ctx = None
            self.btn_live.config(text="GO LIVE TO ZOOM")
            self.vcam_lbl.config(text="Not streaming")
            self.live_lbl.config(text="  STUDIO ON  ", bg=GRN)
            return
        if not HAS_VCAM_LIB:
            messagebox.showerror("Virtual camera library missing", "pyvirtualcam is not installed in this build.")
            return
        W, H = OUT[self.outsize.get()]
        last_err = None
        for backend in ("unitycapture", "obs"):
            try:
                self.vcam_ctx = pyvirtualcam.Camera(width=W, height=H, fps=30, backend=backend)
                self.vcam = self.vcam_ctx.__enter__()
                break
            except Exception as e:
                last_err = e
                self.vcam = self.vcam_ctx = None
        if self.vcam is None:
            messagebox.showerror("Virtual camera driver not found",
                "No virtual camera driver on this laptop yet.\n\n"
                "Run Setup_Virtual_Camera.bat ONCE (it registers the free UnityCapture driver - no OBS needed), "
                "then restart DualCam Studio and press GO LIVE again.\n\nDetails: " + str(last_err))
            return
        self.streaming = True
        self.btn_live.config(text="STOP LIVE")
        self.live_lbl.config(text="  LIVE TO ZOOM  ", bg="#b02020")
        self.vcam_lbl.config(text=f"Streaming to: {self.vcam.device}\nIn Zoom app: Settings > Video > Camera > select that device.")
        if not self.running:
            self.toggle_run()

    def loop(self):
        if not self.running:
            return
        W, H = OUT[self.outsize.get()]
        i1 = self.found[self.cam1.current()] if self.cam1.current() >= 0 else self.found[0]
        i2 = self.found[self.cam2.current()] if self.cam2.current() >= 0 else i1
        frame = self.mix(self._read(i1, self.mirror.get()), self._read(i2), W, H)
        self.last_frame = frame
        if self.streaming and self.vcam is not None:
            try:
                self.vcam.send(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                self.vcam.sleep_until_next_frame()
            except Exception as e:
                self.vcam_lbl.config(text=f"Virtual camera error: {e}")
                self.streaming = False
        if self.writer is not None:
            self.writer.write(frame)
        self.fps_n += 1
        now = time.time()
        if now - self.fps_t >= 1:
            self.fps_lbl.config(text=f"{self.fps_n / (now - self.fps_t):.0f} fps  {W}x{H}")
            self.fps_t, self.fps_n = now, 0
        lvl = min(250, int(self.mic_level * 900))
        self.meter.coords(self.meter_bar, 0, 0, lvl, 16)
        img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        img.thumbnail((820, 470))
        tkimg = ImageTk.PhotoImage(img)
        self.preview.config(image=tkimg)
        self.preview.image = tkimg
        self.after(15, self.loop)

    def toggle_rec(self):
        if self.writer is not None:
            self.writer.release()
            self.writer = None
            self.status.config(text="Recording saved to Videos folder file shown in Save dialog.")
            return
        if self.last_frame is None:
            messagebox.showinfo("Record", "Start the Studio first.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".mp4", initialfile=f"dualcam_{datetime.now():%Y%m%d_%H%M%S}.mp4", filetypes=[("MP4", "*.mp4")])
        if not path:
            return
        W, H = OUT[self.outsize.get()]
        self.writer = cv2.VideoWriter(path, cv2.VideoWriter_fourcc(*"mp4v"), 30, (W, H))
        self.status.config(text=f"Recording video to {path} (mic audio: use Zoom / your recorder - virtual camera carries video, same as OBS).")

    def snapshot(self):
        if self.last_frame is None:
            return
        path = filedialog.asksaveasfilename(defaultextension=".png", initialfile=f"dualcam_{datetime.now():%Y%m%d_%H%M%S}.png", filetypes=[("PNG", "*.png")])
        if path:
            cv2.imwrite(path, self.last_frame)

    def close(self):
        self.running = False
        for c in self.caps.values():
            c.release()
        if self.vcam_ctx:
            try:
                self.vcam_ctx.__exit__(None, None, None)
            except Exception:
                pass
        if self.writer:
            self.writer.release()
        self.destroy()


if __name__ == "__main__":
    Studio().mainloop()
