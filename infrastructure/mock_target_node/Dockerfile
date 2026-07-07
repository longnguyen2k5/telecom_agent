FROM ubuntu:20.04

# Tránh việc apt-get hỏi cấu hình múi giờ khi build
ENV DEBIAN_FRONTEND=noninteractive

# 1. Cài đặt các công cụ cơ bản, SSH Server, Sudo và các thư viện cần thiết để cài Docker
RUN apt-get update && apt-get install -y \
    openssh-server \
    sudo \
    curl \
    gnupg \
    ca-certificates \
    lsb-release \
    stress-ng \
    && rm -rf /var/lib/apt/lists/*

# 2. Cấu hình SSH Server
RUN mkdir /var/run/sshd
RUN useradd -rm -d /home/noc -s /bin/bash -g root -G sudo -u 1000 noc
RUN echo 'noc:123456' | chpasswd
RUN echo "noc ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# 3. CÀI ĐẶT DOCKER ENGINE THẬT TRONG CONTAINER (DOCKER-IN-DOCKER CLI)
RUN mkdir -p /etc/apt/keyrings \
    && curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu focal stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null \
    && apt-get update && apt-get install -y docker-ce docker-ce-cli containerd.io \
    && rm -rf /var/lib/apt/lists/*

# Cấp quyền cho user 'noc' có thể gõ lệnh docker không cần sudo
RUN usermod -aG docker noc

# 4. TẠO SCRIPT GIẢ LẬP TẢI NỀN BIẾN ĐỘNG (Sinh dữ liệu μ, σ thật cho Telemetry)
# Ép tải nền CPU dao động ổn định quanh mức 50% với độ lệch chuẩn cực nhỏ (σ ≈ 2% -> σ² ≈ 4)
RUN apt-get update && apt-get install -y python3 && rm -rf /var/lib/apt/lists/*

RUN cat <<'EOF' > /usr/local/bin/simulate_load.py
import time
import random
import multiprocessing

def target_cpu_load(target_load, duration=10):
    """Giữ tải CPU ổn định ở một mức target_load (%) trong một khoảng thời gian"""
    start_time = time.time()
    while time.time() - start_time < duration:
        # Chạy vòng lặp chiếm dụng CPU trong (target_load / 100) giây
        run_time = target_load / 100.0 / 10.0
        sleep_time = (100.0 - target_load) / 100.0 / 10.0
        
        inner_start = time.time()
        while time.time() - inner_start < run_time:
            pass  # Chiếm dụng CPU
        time.sleep(sleep_time)

def main():
    # Cấu hình Gauss lý tưởng cho môi trường Lab
    MEAN_LOAD = 52.0      # Tải kỳ vọng trung bình mong muốn cố định ở ~52%
    STD_DEV = 2.0         # Độ lệch chuẩn mong muốn chỉ là 2% (Phương sai σ² = 4.0 - cực kỳ chặt chẽ)
    
    print("🚀 Python Smooth Load Generator đang chạy ngầm...")
    while True:
        # Sinh mức tải cho chu kỳ tiếp theo bằng Phân phối chuẩn Gauss (μ, σ)
        # Giúp triệt tiêu hoàn toàn hiện tượng nhảy số giật cục về 0%
        sampled_load = random.gauss(MEAN_LOAD, STD_DEV)
        
        # Đảm bảo chặn trên chặn dưới không bị văng khỏi vùng an toàn
        sampled_load = max(45.0, min(60.0, sampled_load))
        
        # Duy trì mức tải mượt mà này trong vòng 10 giây
        target_cpu_load(target_load=sampled_load, duration=10)

if __name__ == "__main__":
    main()
EOF
RUN chmod +x /usr/local/bin/simulate_load.py

# 5. TẠO SCRIPT KHỞI ĐỘNG HỆ THỐNG (ENTRYPOINT)
# Vì Docker trong Docker cần chạy daemon dockerd lên trước
RUN cat <<'EOF' > /entrypoint.sh
#!/bin/bash
# Khởi động Docker Daemon ngầm
dockerd > /var/log/dockerd.log 2>&1 &

# Đợi Docker Daemon lên hẳn
sleep 3

# Chạy một container giả lập phun log báo lỗi tràn RAM để Agent phân tích
docker run -d --name app-service-crashed alpine sh -c "echo '[INFO] Starting App Service...'; sleep 5; while true; do echo '[WARN] Memory usage high. Triggering GC...'; echo '[ERROR] java.lang.OutOfMemoryError: Java heap space - Cannot allocate memory'; echo '[FATAL] Application crashed. Thread stuck.'; sleep 3; done"

# Chạy script sinh tải nền ngầm
python3 /usr/local/bin/simulate_load.py &

# Khởi động SSH Server ở chế độ foreground
exec /usr/sbin/sshd -D
EOF
RUN chmod +x /entrypoint.sh

EXPOSE 22

ENTRYPOINT ["/entrypoint.sh"]