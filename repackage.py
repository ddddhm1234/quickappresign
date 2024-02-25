import hashlib
import os
import sys
import tempfile
import json
import zipfile

def gen_cert(path: str):
    digests = {}

    for root, dirs, files in os.walk(path):
        for file in files:
            rel_path = os.path.relpath(os.path.join(root, file), path)
            rel_path = rel_path.replace("\\", "/")
            if rel_path.startswith("./"):
                rel_path = rel_path[2:]
            if rel_path.startswith("META-INF") and rel_path != "META-INF/build.txt":
                os.remove(os.path.join(root, file))
                continue
            
            with open(os.path.join(root, file), "rb") as f:
                sha256 = hashlib.sha256(f.read()).hexdigest()
                digests[rel_path] = sha256
    
    hash_dict = {"algorithm": "SHA-256", "digests": digests}

    with zipfile.ZipFile(os.path.join(path, "META-INF", "CERT"), "w") as zip:
        zip.writestr("hash.json", json.dumps(hash_dict))

def zip_folder_with_zipfile(source_folder, output_path):
   with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
      for root, dirs, files in os.walk(source_folder):
         for file in files:
            file_path = os.path.join(root, file)
            archive_path = os.path.relpath(file_path, source_folder)
            zipf.write(file_path, archive_path)

def resign(rpk, output_dir):
    command = 'hap resign --sign "%s" --origin "%s" --file "%s" --dest "%s"' % (
        os.path.abspath(os.path.join(__file__, os.pardir, "sign")),
        os.path.abspath(os.path.join(rpk, os.pardir)),
        os.path.basename(rpk),
        output_dir
    )
    os.system(command)

def main():
    s = r"""
快应用重打包工具, 使用前请安装hap-toolkit, npm install -g hap-toolkit

参数1: 快应用解包目录
参数2: 重打包后的文件名
"""
    if len(sys.argv) < 3:
        print(s)
        exit(1)

    path = sys.argv[1]
    rpk_path = sys.argv[2]
    rpk_name = os.path.basename(rpk_path)
    
    gen_cert(path)

    temp_dir = tempfile.mkdtemp()
    output_rpk = os.path.join(temp_dir, rpk_name)
    zip_folder_with_zipfile(path, output_rpk)

    temp_dir2 = tempfile.mkdtemp()

    resign(os.path.join(temp_dir, rpk_name), temp_dir2)

    os.rename(os.path.join(temp_dir2, rpk_name), rpk_path)


if __name__ == "__main__":
    main()