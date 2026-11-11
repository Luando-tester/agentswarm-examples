<!-- Ban thao do Gemini lam qua Pepper Hunter Doer - CHUA NOP, can duyet truoc khi gui. -->

Dưới đây là file `SOLUTION.md` được phân tích và tổng hợp dựa trên nội dung yêu cầu của issue.

```markdown
# SOLUTION.md - Thêm ví dụ Rust liệt kê bounty mở (Open Bounties)

## 1. Tóm tắt yêu cầu & Tiêu chí nghiệm thu (Acceptance Criteria)

### Tóm tắt yêu cầu:
Thêm một ví dụ nhỏ bằng ngôn ngữ Rust trong thư mục `rust-bounties/` để gọi API công khai và liệt kê các bounty ở trạng thái "open".

### Tiêu chí nghiệm thu:
- **Cấu hình & Biến môi trường**: Đọc biến môi trường `AGENTSWARM_BASE_URL` (giá trị mặc định là `https://agentswarm.space`), tự động cắt bỏ dấu gạch chéo ở cuối (`trailing slashes`).
- **Endpoint gọi API**: Thực hiện HTTP `GET /api/bounties`.
- **Logic lọc & Định dạng đầu ra**:
  - Chỉ lọc các dòng có `status == "open"`.
  - In ra đúng **một dòng UTF-8** cho mỗi bản ghi (theo đúng thứ tự trả về), các trường phân tách bằng ký tự tab (`\t`):
    ```text
    <id>\t<title>\t<bounty.reward>\t<base>/p/<id>
    ```
  - Giữ nguyên chuỗi hiển thị `reward` (verbatim), bảo vệ Unicode, dấu ngoặc kép và thứ tự.
  - Bỏ qua các dòng `closed`. Nếu phản hồi trống hoặc toàn bộ là `closed`, không in gì ra stdout.
- **Xử lý lỗi**: Lỗi HTTP hoặc JSON không hợp lệ (bao gồm rác ở cuối hoặc nhiều document) phải thoát với mã lỗi khác 0 (`nonzero`), xuất thông báo chẩn đoán rõ ràng ra `stderr` và **không có output nào trên stdout**.
- **Phạm vi & Biên dịch**:
  - Không cần API key, không đăng ký hoặc ghi dữ liệu.
  - Entrypoint: `src/main.rs`.
  - Lệnh Build: `cargo build --offline --locked --release`.
  - Lệnh chạy thực tế: `/work/target/release/list-tasks`.
  - Check chạy trong môi trường `--network none`, do đó **phải** cung cấp `Cargo.lock` và cây `vendor` đầy đủ (hoặc sử dụng API có sẵn).
- **Tài liệu & Phạm vi thay đổi (Scope)**:
  - Thêm `rust-bounties/` (source code, manifests/lockfiles, thư mục vendor nếu có, và `README.md` bao gồm điều kiện tiên quyết, cách chạy, cài đặt base-URL và link tuỳ chọn tới `https://agentswarm.space/skill.md`).
  - Thêm 1 dòng điều hướng (navigation) ở file `README.md` gốc của repo.

---

## 2. Cách tiếp cận kỹ thuật từng bước

1. **Khởi tạo dự án Rust**:
   - Tạo thư mục `rust-bounties/` và khởi tạo ứng dụng Cargo (`cargo init --bin`).
2. **Xử lý Dependencies (Offline Mode)**:
   - Thêm các thư viện cần thiết cho HTTP client (ví dụ: `ureq` hoặc `isahc`/`minreq` bản nhẹ để dễ vendor hoặc không phụ thuộc C bindings phức tạp) và JSON parsing (`serde`, `serde_json`).
   - Cấu hình `.cargo/config.toml` để vendor các dependency nếu cần thiết, đảm bảo chạy thành công với `cargo build --offline --locked --release`.
3. **Phát triển Logic chính (`src/main.rs`)**:
   - Lấy biến môi trường `AGENTSWARM_BASE_URL`, dùng giá trị mặc định `https://agentswarm.space` nếu chưa thiết lập, và loại bỏ ký tự `/` ở cuối nếu có.
   - Thực hiện HTTP GET tới `${BASE_URL}/api/bounties`.
   - Bắt lỗi HTTP, trả về exit code khác 0 và ghi log vào `stderr` nếu có lỗi kết nối/phản hồi không hợp lệ.
   - Parse cú pháp JSON theo cấu trúc `{"bounties": [...]}` sử dụng `serde_json`. Xử lý lỗi nếu JSON malformed.
   - Duyệt qua danh sách `bounties`, lọc phần tử có `status == "open"`.
   - In ra stdout theo đúng định dạng yêu cầu bằng các ký tự phân tách tab `\t`.
4. **Viết tài liệu (`rust-bounties/README.md`)**:
   - Mô tả điều kiện tiên quyết (Prerequisites), hướng dẫn biên dịch và thực thi, cấu hình base-URL, và liên kết tuỳ chọn tới `https://agentswarm.space/skill.md`.
5. **Cập nhật Root README**:
   - Thêm một dòng điều hướng trỏ tới ví dụ `rust-bounties/` mới tạo.

---

## 3. File / Đường dẫn dự kiến sửa / tạo mới

*(Lưu ý: Cấu trúc dựa trên yêu cầu trong issue)*

- **Tạo mới**: `rust-bounties/Cargo.toml`
- **Tạo mới**: `rust-bounties/Cargo.lock`
- **Tạo mới**: `rust-bounties/src/main.rs`
- **Tạo mới**: `rust-bounties/README.md`
- **Tạo mới (nếu dùng vendor offline)**: `rust-bounties/.cargo/config.toml` và thư mục vendor tương ứng.
- **Sửa đổi**: `README.md` (Gốc của repo - thêm 1 dòng điều hướng).

---

## 4. Kế hoạch tự test (Self-Test Plan)

Chạy bộ test chính thức từ task-check được cung cấp trong issue để đảm bảo tính chính xác trước khi mở PR:

```bash
# 1. Thiết lập biến môi trường và đồng bộ môi trường kiểm thử
export BOUNTY_REPO=/absolute/path/to/your/agentswarm-examples
cd agentswarm-examples-checks
git checkout 5cd882709a68263f3f09e16f1a9471da0e0f9a99
uv sync --project task-checks --locked --python 3.11
source task-checks/.venv/bin/activate

# 2. Đảm bảo các image Docker đã được pull sẵn
docker pull rust:1.89@sha256:57407b378b2b6e07b48a6135a20c87cc22ea6e249c0acf6cb1833ead3cf116e9
docker pull python:3.12-slim@sha256:5e2bdb1b0d542d5039cffb8181c65930093949194a65c365dfb1b0fe13a4fa5b

# 3. Chạy Pytest kiểm tra code example cho Rust
EXAMPLE_LANGUAGE=rust python -m pytest -q task-checks/code-example-list-bounties/test_list_bounties.py
```
```
