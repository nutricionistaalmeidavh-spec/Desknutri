from __future__ import annotations
import argparse
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization

def main():
    ap=argparse.ArgumentParser(description='Cria par Ed25519 exclusivo para assinatura das releases do NutriDesktop.')
    ap.add_argument('out_dir');a=ap.parse_args();out=Path(a.out_dir);out.mkdir(parents=True,exist_ok=True)
    private=Ed25519PrivateKey.generate();pub=private.public_key()
    priv_path=out/'update_private.pem';pub_path=out/'update_public.pem'
    priv_path.write_bytes(private.private_bytes(serialization.Encoding.PEM,serialization.PrivateFormat.PKCS8,serialization.NoEncryption()))
    pub_path.write_bytes(pub.public_bytes(serialization.Encoding.PEM,serialization.PublicFormat.SubjectPublicKeyInfo))
    print(f'PRIVATE (não distribuir): {priv_path}')
    print(f'PUBLIC (copiar para config/update_public.pem): {pub_path}')
if __name__=='__main__':main()
