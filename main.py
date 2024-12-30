import machine
import time
import _thread
from module_manager import ModuleManager
import ports
from rezistance_detector import read_pins

# Start the pin-reading thread
_thread.start_new_thread(read_pins, ())


def display_menu():
    try:
        while True:
            print("\n--- Module Manager Menu ---")
            print("1. List All Modules")
            print("2. Get Module Info")
            print("3. List All Ports")
            print("4. Monitor Dynamic States")
            print("5. Get State by UUID")
            print("6. Set State by UUID")
            print("7. Exit")
            
            choice = input("Enter your choice: ").strip()
            if choice == "1":
                print("\n--- Active Modules ---")
                for uuid, module in ModuleManager.modules.items():
                    print("UUID: {}, Type: {}, Port: {}".format(uuid, type(module).__name__, module.port.identification_pin))

            elif choice == "2":
                uuid_input = input("Enter module UUID to retrieve: ").strip()
                try:
                    module = ModuleManager.get_module(uuid_input)
                    if module:
                        print("Module Info: Type={}, State={}, Port={}".format(
                            type(module).__name__, module.get_state(), module.port.identification_pin
                        ))
                    else:
                        print("No module found with that UUID.")
                except Exception as e:
                    print("Error: {}".format(e))

            elif choice == "3":
                print("\n--- Port Status ---")
                for port_number, port in ports.available_ports.items():
                    module = port.get_module()
                    module_info = (
                        "Module (Type: {}, State: {})".format(type(module).__name__, module.get_state())
                        if module else "None"
                    )
                    print("Port {}: {}".format(port_number, module_info))

            elif choice == "4":
                print("Monitoring dynamic states (Press Ctrl+C to stop):")
                try:
                    while True:
                        for port_number, port in ports.available_ports.items():
                            module = port.get_module()
                            module_info = (
                                "Module (Type: {}, State: {})".format(type(module).__name__, module.get_state())
                                if module else "None"
                            )
                            print("Port {}: {}".format(port_number, module_info))
                        time.sleep(1)
                except KeyboardInterrupt:
                    print("Stopped monitoring.")

            elif choice == "5":
                uuid_input = input("Enter module UUID to get state: ").strip()
                try:
                    module = ModuleManager.get_module(uuid_input)
                    if module:
                        print("State for Module (UUID={}): {}".format(uuid_input, module.get_state()))
                    else:
                        print("No module found with that UUID.")
                except Exception as e:
                    print("Error: {}".format(e))

            elif choice == "6":
                uuid_input = input("Enter module UUID to set state: ").strip()
                try:
                    new_state = input("Enter new state: ").strip()
                    module = ModuleManager.get_module(uuid_input)
                    if module:
                        module.set_state(new_state)
                        print("State updated successfully for Module (UUID={})".format(uuid_input))
                    else:
                        print("No module found with that UUID.")
                except Exception as e:
                    print("Error: {}".format(e))

            elif choice == "7":
                print("Exiting menu. Goodbye!")
                break

            else:
                print("Invalid choice. Please try again.")
    except KeyboardInterrupt:
        print("\nExiting due to user interrupt. Goodbye!")

if __name__ == "__main__":
    display_menu()
