# Mã lỗi

Mỗi lỗi có một `code` ổn định. Danh mục dưới đây được lấy nguyên từ
[`docs/api-errors.md`](https://github.com/quinguyen1502/superstep/blob/develop/docs/api-errors.md);
`backend/tests/test_api_envelope.py` đối chiếu file này với
`backend/app/core/errors.py` và cả hai file ngôn ngữ của UI, nên danh mục luôn
đầy đủ. Thông điệp trong bảng là tiếng Anh; UI hiện bản dịch tiếng Việt theo
`code`.

Hình dạng response có ở [HTTP API](api.md#envelope).

--8<-- "docs/api-errors.md:catalog"
