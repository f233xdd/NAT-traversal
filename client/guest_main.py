# run this file to start your visitor client
import time
import ctypes
import threading

import client


def start(server_addr: tuple[str, int] | None = None,
          virtual_port: int | None = None,
          crypt: bool | None = None,
          public=None,
          daemon=False):
    addr, port, is_crypt = client.get_attrs("guest")

    if server_addr is not None:
        addr = server_addr

    if virtual_port is not None:
        port = virtual_port

    if crypt is not None:
        is_crypt = crypt

    if public:
        log = client.get_log("guest", public)
    else:
        log = client.get_log("guest")

    log.info(f"is_crypt: {is_crypt}")

    guest = client.GuestClient(addr, port, is_crypt, log)

    functions = [guest.send_server_data, guest.get_server_data]

    if __name__ == "__main__":
        daemon = True

    threads = [threading.Thread(target=func, daemon=daemon) for func in functions]

    for thread in threads:
        thread.start()

    threads.extend(guest.local_server_main(daemon=daemon))
    print(threads)

    killed = False
    while True:
        for _thd in threads:
            if not _thd.is_alive():
                print("NOT ALIVE")
                for thd in threads:  # interrupt threads
                    ctypes.pythonapi.PyThreadState_SetAsyncExc(thd.native_id, ctypes.py_object(SystemExit))

                while True:  # check threads
                    time.sleep(1)
                    all_not_alive = True
                    for thd in threads:
                        if thd.is_alive():
                            all_not_alive = False
                    if all_not_alive:
                        killed = True
                        break

                break
        if killed:
            log.info("exit successfully")
            break
        time.sleep(1)


def main(server_addr: tuple[str, int] | None = None,
         virtual_port: int | None = None,
         public=None):
    try:
        start(server_addr, virtual_port, public)
    except KeyboardInterrupt as e:
        print("Canceled by [Ctrl-C]")
        print(e)


if __name__ == "__main__":
    main()
