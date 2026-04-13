from decimal import Decimal, InvalidOperation

from django.db.models import Q
from rest_framework import permissions, viewsets
from rest_framework.exceptions import ValidationError

from modules.jobs.models import TinTuyenDung
from modules.jobs.serializers import TinTuyenDungSerializer


class TinTuyenDungViewSet(viewsets.ModelViewSet):
	serializer_class = TinTuyenDungSerializer
	default_queryset = TinTuyenDung.objects.select_related("cong_ty").all().order_by("-tao_luc")
	public_actions = {"list", "retrieve"}
	default_status = TinTuyenDung.TrangThai.DANG_MO
	allowed_statuses = {choice for choice, _label in TinTuyenDung.TrangThai.choices}

	def get_permissions(self):
		if self.action in self.public_actions:
			return [permissions.AllowAny()]
		return [permissions.IsAuthenticated()]

	def get_queryset(self):
		queryset = self.default_queryset
		query_params = self.request.query_params

		status = query_params.get("trang_thai", "").strip() or self.default_status
		if status not in self.allowed_statuses:
			raise ValidationError({"trang_thai": "Gia tri trang_thai khong hop le."})

		queryset = queryset.filter(trang_thai=status)

		keyword = query_params.get("q", "").strip()
		if keyword:
			queryset = queryset.filter(Q(tieu_de__icontains=keyword) | Q(noi_dung__icontains=keyword))

		location = query_params.get("dia_diem", "").strip()
		if location:
			queryset = queryset.filter(dia_diem_lam_viec__icontains=location)

		wage_min = query_params.get("luong_min", "").strip()
		if wage_min:
			try:
				minimum_salary = Decimal(wage_min)
			except InvalidOperation as exc:
				raise ValidationError({"luong_min": "luong_min phai la so hop le."}) from exc

			queryset = queryset.filter(luong_theo_gio__gte=minimum_salary)

		return queryset
