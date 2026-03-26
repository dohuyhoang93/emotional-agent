"""
DEPRECATED: context_helpers.py — ContextGuard Bypass Layer
==========================================================
Tệp này đã bị VÔ HIỆU HÓA hoàn toàn.

Trước đây, file này chứa các hàm get_domain_ctx(), get_attr(), set_attr()
dùng để vượt rào ContextGuard bằng cách truy cập trực tiếp _inner._target.
Điều này khiến Rust Engine bị "mù" trước các thay đổi trạng thái, dẫn đến
lỗi mất dữ liệu nghiêm trọng (INC-019, INC-020).

Toàn bộ 16 Process files đã được tái cấu trúc về Pure POP Architecture,
sử dụng getattr(ctx.domain, ...) trực tiếp qua ContextGuard.

Ngày: 2026-03-24
Xem: analysis_implicit_vs_explicit.md
"""

raise ImportError(
    "context_helpers.py đã bị VÔ HIỆU HÓA. "
    "Sử dụng getattr(ctx.domain, 'X', default) thay cho get_domain_ctx/get_attr/set_attr. "
    "Xem: INC-019, INC-020, analysis_implicit_vs_explicit.md"
)
