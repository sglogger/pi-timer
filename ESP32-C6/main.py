import machine
import bluetooth
import time
import st7789
import framebuf

# --- KONFIGURATION & UUIDs ---
NAME = "SwiNOG-Pi-Timer"
UUID_SER = bluetooth.UUID("48593a1c-333e-469b-8664-d1303867d341")
UUID_CHR = bluetooth.UUID("9f3c7b34-8c34-4503-b91d-06900f917531")

# --- DEINE SPEZIAL-FARBEN (Byte-Swapped BGR) ---
BLACK  = 0x0000
WHITE  = 0xFFFF
GREEN  = 0xE007
YELLOW = 0xFF07
ORANGE = 0x5F03
RED    = 0x1F00

_IRQ_CONNECT    = 1
_IRQ_DISCONNECT = 2
_IRQ_WRITE      = 3

# --- DISPLAY SETUP ---
bl_pin = machine.Pin(22, machine.Pin.OUT)
spi = machine.SPI(1, baudrate=40000000, sck=machine.Pin(7), mosi=machine.Pin(6))
tft = st7789.ST7789(spi, 172, 320, 
    reset=machine.Pin(21, machine.Pin.OUT),
    dc=machine.Pin(15, machine.Pin.OUT),
    cs=machine.Pin(14, machine.Pin.OUT),
    backlight=bl_pin,
    rotation=1
)

def draw_big_text(text, x, y, size, color):
    char_buf = bytearray(8 * 8 // 8) 
    fb_char = framebuf.FrameBuffer(char_buf, 8, 8, framebuf.MONO_HLSB)
    for i, char in enumerate(text):
        fb_char.fill(0)
        fb_char.text(char, 0, 0, 1)
        for py in range(8):
            for px in range(8):
                if fb_char.pixel(px, py):
                    tft.fill_rect(x + (i * 8 * size) + (px * size), 
                                  y + (py * size), size, size, color)

class BLETimer:
    def __init__(self):
        self.ble = bluetooth.BLE()
        self.ble.active(True)
        self.ble.irq(self._irq)
        service = (UUID_SER, ((UUID_CHR, bluetooth.FLAG_WRITE | bluetooth.FLAG_READ),),)
        ((self.handle,),) = self.ble.gatts_register_services((service,))
        self.running = False
        self.new_seconds = None
        self.stop_requested = False
        self._advertise()

    def _advertise(self):
        short_name = "SwiNOG" 
        adv_name = short_name.encode()
        uuid_bytes = bytes([0x41, 0xd3, 0x67, 0x38, 0x30, 0xd1, 0x64, 0x86, 0x9b, 0x46, 0x3e, 0x33, 0x1c, 0x3a, 0x59, 0x48])
        payload = bytearray(b'\x02\x01\x06') + bytearray([len(adv_name) + 1, 0x09]) + adv_name + bytearray([len(uuid_bytes) + 1, 0x07]) + uuid_bytes
        self.ble.gap_advertise(100, payload)

    def _irq(self, event, data):
        if event == _IRQ_CONNECT: print("[BLE] Verbunden")
        elif event == _IRQ_DISCONNECT: self._advertise()
        elif event == _IRQ_WRITE:
            conn_handle, value_handle = data
            raw_msg = self.ble.gatts_read(value_handle).decode().strip().upper()
            if raw_msg.startswith("START:"):
                try:
                    self.new_seconds = int(raw_msg.split(":")[1])
                    self.running = True
                    self.stop_requested = False
                except: pass
            elif raw_msg == "STOP":
                self.running = False
                self.stop_requested = True

# --- HAUPTPROGRAMM ---
ble_timer = BLETimer()
diff = 0
is_init = True 
last_second_tick = time.ticks_ms()

while True:
    current_tick = time.ticks_ms()

    if ble_timer.stop_requested:
        bl_pin.value(0)
        ble_timer.stop_requested = False
        is_init = False
        continue

    if ble_timer.new_seconds is not None:
        diff = ble_timer.new_seconds - 0 		# bluetooth delay anpassen, jetzt 0
        ble_timer.new_seconds = None
        is_init = False
        bl_pin.value(1)
        last_second_tick = current_tick

    # Sekunden-Countdown (Non-blocking)
    if ble_timer.running and not is_init:
        if time.ticks_diff(current_tick, last_second_tick) >= 1000:
            diff -= 1
            last_second_tick = current_tick

    tft.fill(BLACK)

    if is_init:
        draw_big_text("READY...", 55, 55, 3, WHITE)
        draw_big_text("SwiNOG Timer ready to connect", 55, 85, 1, WHITE)
        draw_big_text("v0.9.3", 250, 140, 1, WHITE)
    
    else:
        border_needed = False
        
        # Blink- & Farblogik
        if diff <= 0:
            is_on = (current_tick // 500) % 2 == 0
            current_color = RED if is_on else BLACK
            border_needed = True
        elif diff < 60:
            current_color = ORANGE
            border_needed = True
        elif diff < 300:
            current_color = YELLOW
        else:
            current_color = GREEN

        # 5 Pixel dicker Rahmen (nur wenn Farbe nicht BLACK)
        if border_needed and current_color != BLACK:
            for i in range(5):
                tft.rect(i, i, tft.width - (2 * i), tft.height - (2 * i), current_color)

        # Zeit formatieren
        abs_diff = abs(diff)
        m, s = divmod(abs_diff, 60)
        prefix = "-" if diff < 0 else ""
        zeit_text = "{}{:02d}:{:02d}".format(prefix, m, s)
        
        x_pos = 25 if diff < 0 else 45
        draw_big_text(zeit_text, x_pos, 60, 6, current_color)

    tft.show()
    time.sleep_ms(10) # Kleine Entlastung für den ESP32

