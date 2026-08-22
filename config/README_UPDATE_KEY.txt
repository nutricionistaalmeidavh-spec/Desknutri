ATUALIZACOES ASSINADAS - NUTRIDESKTOP

1. Gere o par fora do repositorio:
   python tools/update_key_admin.py C:\Segredos\NutriDesktop
2. Copie SOMENTE update_public.pem para esta pasta como config\update_public.pem.
3. Mantenha update_private.pem fora do repositorio e fora do instalador.
4. Configure UPDATE_SIGNING_PRIVATE_KEY_B64 como GitHub Actions Secret apenas se for usar o workflow de release.
