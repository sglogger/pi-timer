import asyncio
from bleak import BleakScanner, BleakClient

SERVICE_UUID = "48593a1c-333e-469b-8664-d1303867d341"
CHARACTERISTIC_UUID = "9f3c7b34-8c34-4503-b91d-06900f917531"

async def main():
    print("Suche nach dem Timer (Name oder UUID)...")

    def filter_handler(device, ad):
        # Treffer wenn Name passt ODER die UUID im Paket ist
        name = device.name or ""
        has_uuid = SERVICE_UUID.lower() in [s.lower() for s in ad.service_uuids]
        return "SWINOG" in name.upper() or has_uuid

    device = await BleakScanner.find_device_by_filter(filter_handler, timeout=10.0)

    if not device:
        print("\nNicht gefunden. Probiere es mit einem kompletten Scan...")
        # Fallback: Liste einfach alles auf
        devices = await BleakScanner.discover()
        for d in devices:
            print(f"Gefunden: {d.name} [{d.address}]")
        return

    print(f"Gefunden: {device.name} ({device.address})")
    
    async with BleakClient(device) as client:
        print("Verbunden! Sende Test START:10...")
        #await client.write_gatt_char(CHARACTERISTIC_UUID, b"START:10", response=True)
        
        while True:
            cmd = input("\nSekunden oder STOP: ").strip().upper()
            if cmd == "EXIT": break
            payload = "STOP" if cmd == "STOP" else f"START:{cmd}"
            await client.write_gatt_char(CHARACTERISTIC_UUID, payload.encode(), response=True)

if __name__ == "__main__":
    asyncio.run(main())
