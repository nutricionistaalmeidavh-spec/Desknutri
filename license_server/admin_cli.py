from __future__ import annotations
import argparse, getpass, shutil
from pathlib import Path
from .core import AdminService, LicenseSigner, LicenseStore, ServerPaths

def main():
    p=argparse.ArgumentParser(description='Administração inicial do servidor de licenças NutriDesktop')
    sub=p.add_subparsers(dest='cmd',required=True)
    a=sub.add_parser('init-admin');a.add_argument('--email',required=True);a.add_argument('--password')
    sub.add_parser('init-keys')
    cp=sub.add_parser('copy-public-key');cp.add_argument('--to',required=True)
    args=p.parse_args();paths=ServerPaths.from_env();store=LicenseStore(paths.db_path);store.initialize()
    if args.cmd=='init-admin':
        password=args.password or getpass.getpass('Senha administrativa: ');aid=AdminService(store).create_admin(args.email,password);print(f'Administrador criado: id={aid}')
    elif args.cmd=='init-keys':
        if paths.private_key.exists() or paths.public_key.exists():raise SystemExit('As chaves já existem. Remova-as manualmente somente se realmente quiser rotacionar.')
        LicenseSigner.generate(paths.private_key,paths.public_key);print(f'Privada: {paths.private_key}\nPública: {paths.public_key}')
    elif args.cmd=='copy-public-key':
        if not paths.public_key.exists():raise SystemExit('Gere as chaves primeiro com init-keys.')
        dest=Path(args.to);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(paths.public_key,dest);print(f'Chave pública copiada para {dest}')

if __name__=='__main__':main()
