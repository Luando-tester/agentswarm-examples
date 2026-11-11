<!-- Ban thao do Gemini lam qua Pepper Hunter Doer - CHUA NOP, can duyet truoc khi gui. -->

Dưới đây là tài liệu **SOLUTION.md** chi tiết phân tích yêu cầu và kế hoạch triển khai giải pháp dựa trên nội dung issue.

---

# SOLUTION.md: TypeScript Example - List Open Bounties

## 1. Tóm tắt yêu cầu & Tiêu chí nghiệm thu (Trích từ Issue)

### Yêu cầu chính
* **Mục tiêu**: Tạo một ví dụ TypeScript nhỏ trong thư mục `typescript-bounties/` thực hiện truy vấn API công khai `GET /api/bounties` để liệt kê các bounty đang mở (`status == "open"`).
* **Entrypoint**: `typescript-bounties/example.ts`.
* **Cách chạy**: Chạy trực tiếp bằng `node --experimental-strip-types example.ts` (sử dụng Node.js v22 tích hợp sẵn, không cài đặt thêm dependency bên ngoài).
* **Biến môi trường**: Đọc `AGENTSWARM_BASE_URL` (giá trị mặc định: `https://agentswarm.space`). Cần xóa các dấu `/` ở cuối chuỗi (`trim trailing slashes`).
* **Định dạng đầu ra (stdout)**:
  * Với mỗi record có `status == "open"`, in chính xác 1 dòng UTF-8 theo đúng thứ tự trả về từ API, phân tách bằng ký tự Tab (`\t`):
    ```text
    <id>\t<title>\t<bounty.reward>\t<base>/p/<id>
    ```
  * Giữ nguyên chuỗi hiển thị reward (bao gồm đơn vị/tiền tệ), Unicode, dấu ngoặc và thứ tự dữ liệu.
  * Bỏ qua các record đã đóng (`closed`).
  * Trường hợp danh sách rỗng hoặc tất cả đều đóng: Không in gì ra `stdout` (stdout trống).
* **Xử lý lỗi**:
  * Khi gặp lỗi HTTP hoặc JSON không hợp lệ (bao gồm dữ liệu thừa ở cuối/trailing garbage, hoặc chứa nhiều tài liệu JSON/multiple documents): Phải thoát với mã lỗi khác 0 (`exit nonzero`), in thông báo chẩn đoán rõ ràng ra `stderr`, và **hoàn toàn không** in gì ra `stdout`.
* **Phạm vi không làm (Out of scope)**:
  * Không phân trang (pagination) - chỉ lấy duy nhất trang dữ liệu đầu tiên được trả về.
  * Không sử dụng API key, không thực hiện đăng ký hay ghi dữ liệu (read-only).
* **Tài liệu đính kèm**:
  * Tạo `typescript-bounties/README.md` mô tả điều kiện tiên quyết, cách chạy, cấu hình `AGENTSWARM_BASE_URL`, và đường dẫn tùy chọn đến `https://agentswarm.space/skill.md`. Nếu có ví dụ đăng ký tùy chọn trong README, sử dụng `"foundVia":"examples-v1"`.
  * Thêm 1 dòng điều hướng chỉ đến ví dụ TypeScript trong `README.md` ở thư mục gốc của repository.

### Tiêu chí nghiệm thu (Acceptance Criteria)
* Tất cả kiểm thử tự động trong `task-checks/code-example-list-bounties/test_list_bounties.py` vượt qua thành công với lệnh:
  ```bash
  EXAMPLE_LANGUAGE=typescript python -m pytest -q task-checks/code-example-list-bounties/test_list_bounties.py
  ```
* Test suite sẽ chạy code trong môi trường Docker cách ly hoàn toàn mạng (`--network none`).
* Bộ test bao gồm các kịch bản ngẫu nhiên: thay đổi ID, Unicode title, thứ tự, số lượng bounty mở, lỗi HTTP và malformed JSON.

---

## 2. Cách tiếp cận kỹ thuật từng bước (Step-by-Step Technical Approach)

### Bước 1: Xử lý cấu hình và Base URL
* Lấy giá trị biến môi trường `process.env.AGENTSWARM_BASE_URL`.
* Nếu không có, mặc định là `https://agentswarm.space`.
* Cắt bỏ tất cả ký tự `/` ở cuối chuỗi URL để đảm bảo định dạng chuẩn khi ghép đường dẫn.

### Bước 2: Thực hiện yêu cầu HTTP GET (sử dụng Node.js built-in `fetch`)
* Tạo URL truy vấn: `${baseUrl}/api/bounties`.
* Gọi API bằng `fetch(url)`.
* Bắt lỗi mạng/kết nối: Nếu quá trình `fetch` thất bại, in thông báo lỗi ra `console.error` (stderr) và gọi `process.exit(1)`.

### Bước 3: Đọc và Validation dữ liệu HTTP Response
* Kiểm tra `response.ok` (status code trong khoảng 200–299). Nếu không đạt (ví dụ 404, 500):
  * In thông báo lỗi HTTP chi tiết ra `stderr`.
  * Gọi `process.exit(1)` (không in bất kỳ dữ liệu nào ra stdout).

### Bước 4: Kiểm tra và Parsing JSON chặt chẽ
* Lấy toàn bộ nội dung phản hồi dưới dạng text: `const text = await response.text()`.
* Tiến hành phân tích chuỗi JSON:
  * Kiểm tra cú pháp JSON hợp lệ và đảm bảo không có văn bản thừa phía sau (trailing garbage) hoặc chứa nhiều JSON document liên tiếp.
  * Nếu quá trình parse thất bại hoặc phát hiện malformed JSON, in chẩn đoán lỗi ra `stderr` và `process.exit(1)`.

### Bước 5: Phân tích cấu trúc Dữ liệu và In đầu ra
* Kiểm tra cấu trúc object phản hồi theo schema: `{"bounties": [...]}`.
* Duyệt qua mảng `bounties` theo đúng thứ tự trả về:
  * Lọc các phần tử có `item.status === "open"`.
  * Với mỗi phần tử mở, tạo chuỗi đầu ra:
    ```typescript
    `${item.id}\t${item.title}\t${item.bounty.reward}\t${baseUrl}/p/${item.id}`
    ```
  * In ra `stdout` bằng `console.log()` hoặc `process.stdout.write()`.

### Bước 6: Soạn thảo Tài liệu
* Tạo `typescript-bounties/README.md` mô tả cách chạy bằng `node --experimental-strip-types example.ts`, biến môi trường `AGENTSWARM_BASE_URL`, link tham khảo `skill.md`, và giá trị `"foundVia":"examples-v1"` cho kịch bản đăng ký (nếu đề cập).
* Cập nhật `README.md` gốc để thêm 1 dòng liên kết điều hướng tới ví dụ TypeScript này.

---

## 3. File / Đường dẫn dự kiến sửa đổi

Các file nằm trong phạm vi cho phép của issue:

| Đường dẫn file | Trạng thái | Nội dung / Mục đích |
| :--- | :--- | :--- |
| `typescript-bounties/example.ts` | **Tạo mới** (Dự kiến) | Mã nguồn chính (Entrypoint) xử lý gọi API và in danh sách bounties |
| `typescript-bounties/README.md` | **Tạo mới** (Dự kiến) | Tài liệu hướng dẫn sử dụng, yêu cầu môi trường và cấu hình |
| `README.md` | **Chỉnh sửa** (Dự kiến) | Thêm 1 dòng điều hướng dẫn đến thư mục `typescript-bounties/` |

---

## 4. Kế hoạch tự kiểm thử (Self-Testing Plan)

### A. Tự kiểm thử thủ công local (Manual Test Cases)
1. **Trường hợp chuẩn (Happy Path)**:
   * Chạy với URL mặc định hoặc mock server trả về danh sách bounties chuẩn.
   * Xử lý chính xác UTF-8, ký tự tab `\t`, giữ nguyên tiền tệ/đơn vị reward.
2. **Trường hợp URL có trailing slash**:
   * Thiết lập `AGENTSWARM_BASE_URL="https://agentswarm.space/"` và kiểm tra URL đầu ra ở cột 4 không bị lặp dấu `/` (`/p/<id>`).
3. **Trường hợp Không có bounty mở / Danh sách rỗng**:
   * Phản hồi trả về chỉ toàn status `"closed"` hoặc mảng rỗng -> Kết quả `stdout` phải hoàn toàn trống.
4. **Trường hợp Lỗi HTTP**:
   * Giả lập response HTTP 404/500 -> Chương trình thoát với code khác 0, `stderr` có log lỗi, `stdout` rỗng.
5. **Trường hợp Malformed JSON**:
   * JSON bị lỗi cú pháp, JSON có trailing garbage (vd: `{"bounties":[]} extra_text`), hoặc nhiều JSON docs -> Chương trình thoát với code khác 0, `stderr` có log lỗi, `stdout` rỗng.

### B. Chạy hệ thống kiểm thử tự động của Repository (Automated Task Checks)
Thực hiện chính xác các bước kiểm thử theo công ước đã chỉ định trong issue:

```bash
# 1. Thiết lập biến môi trường chỉ đến thư mục checkout
export BOUNTY_REPO=/absolute/path/to/your/agentswarm-examples

# 2. Clone repository chứa test runner và checkout đúng commit contract
git clone https://github.com/andrewsiah/agentswarm-examples agentswarm-examples-checks
cd agentswarm-examples-checks
git checkout 5cd882709a68263f3f09e16f1a9471da0e0f9a99

# 3. Khởi tạo môi trường Python 3.11 với uv
uv sync --project task-checks --locked --python 3.11
source task-checks/.venv/bin/activate

# 4. Tải các Docker images cần thiết cho môi trường test isolated
docker pull node:22@sha256:7702d8aa4d5910871692af4480eb3ba86f23047a6417a44d857d06c95d060d3f
docker pull python:3.12-slim@sha256:5e2bdb1b0d542d5039cffb8181c65930093949194a65c365dfb1b0fe13a4fa5b

# 5. Chạy test suite cho ngôn ngữ TypeScript
EXAMPLE_LANGUAGE=typescript python -m pytest -q task-checks/code-example-list-bounties/test_list_bounties.py
```
