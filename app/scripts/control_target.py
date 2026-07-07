#!/usr/bin/env python3
import subprocess
import sys

TARGET_CONTAINER = "mock-target-node"

def is_container_running(container_name):
    try:
        output = subprocess.check_output(
            ["docker", "ps", "--format", "{{.Names}}"], 
            stderr=subprocess.STDOUT
        ).decode("utf-8")
        return container_name in output.split('\n')
    except subprocess.CalledProcessError:
        return False

def run_docker_exec(command, detach=False):
    base_cmd = ["docker", "exec"]
    if detach:
        base_cmd.append("-d")
    base_cmd.append(TARGET_CONTAINER)
    
    # command is a string, split it
    full_cmd = base_cmd + command.split()
    
    try:
        if detach:
            subprocess.Popen(full_cmd)
        else:
            subprocess.run(full_cmd, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Lỗi khi thực thi lệnh: {e}")
        return False

def print_menu():
    print("==========================================")
    print("    TELECOM AGENT - TARGET CONTROLLER     ")
    print("==========================================")
    print("Hệ thống giả lập môi trường Node mục tiêu (mock-target-node)")
    print("để test các kịch bản của Agent.")
    print("------------------------------------------")
    print("1. Giả lập CPU cao (> threshold) trong 120s")
    print("   -> Phù hợp test kịch bản restart service")
    print("2. Giả lập RAM cao (> threshold) trong 120s")
    print("   -> Phù hợp test kịch bản check logs")
    print("3. Giả lập quá tải (RAM & CPU > threshold) trong 120s")
    print("   -> Phù hợp test kịch bản restart docker daemon")
    print("4. Dừng mọi giả lập tải (Kill stress-ng)")
    print("------------------------------------------")
    print("5. Stop container 'app-service-crashed' bên trong target")
    print("6. Start container 'app-service-crashed' bên trong target")
    print("0. Thoát")
    print("==========================================")

def main():
    if not is_container_running(TARGET_CONTAINER):
        print(f"LỖI: Container {TARGET_CONTAINER} không hoạt động.")
        print("Vui lòng chạy 'docker-compose up -d' ở thư mục gốc trước.")
        sys.exit(1)

    while True:
        print_menu()
        try:
            choice = input("Chọn hành động (0-6): ").strip()
        except KeyboardInterrupt:
            print("\nThoát chương trình.")
            sys.exit(0)

        if choice == '1':
            print("Đang tạo tải CPU...")
            run_docker_exec("stress-ng --cpu 4 --cpu-load 95 --timeout 120s", detach=True)
            print("Thành công! Hãy yêu cầu Agent kiểm tra health của node.")
        elif choice == '2':
            print("Đang tạo tải RAM (không ăn CPU)...")
            run_docker_exec("stress-ng --vm 1 --vm-bytes 85% --vm-hang 120 --timeout 120s", detach=True)
            print("Thành công! Hãy yêu cầu Agent kiểm tra health của node.")
        elif choice == '3':
            print("Đang tạo tải CPU & RAM...")
            run_docker_exec("stress-ng --cpu 4 --cpu-load 95 --vm 1 --vm-bytes 85% --timeout 120s", detach=True)
            print("Thành công! Hãy yêu cầu Agent kiểm tra health của node.")
        elif choice == '4':
            print("Đang dừng tải...")
            # pkill có thể trả về lỗi nếu không có process nào
            subprocess.run(["docker", "exec", TARGET_CONTAINER, "pkill", "stress-ng"])
            print("Thành công!")
        elif choice == '5':
            print("Đang stop container Nginx...")
            run_docker_exec("docker stop app-service-crashed")
            print("Thành công!")
        elif choice == '6':
            print("Đang start container Nginx...")
            run_docker_exec("docker start app-service-crashed")
            print("Thành công!")
        elif choice == '0':
            print("Thoát chương trình.")
            break
        else:
            print("Lựa chọn không hợp lệ, vui lòng thử lại.\n")

if __name__ == "__main__":
    main()
