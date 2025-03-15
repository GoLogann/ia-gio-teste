#!/bin/bash

if [[ ! $1 || ! $2 ]]; then
    echo "É necessário passar a versão atual e a nova."
    echo "Ex.: ./release.sh 2.2.29 2.3.0"
    exit 1;
fi;

echo "Atualizando da versão $1 para $2..."

echo "Versões atualizadas. Compilando projeto..."

# Atualiza dependências e compila o projeto Python
pip install -r requirements.txt

filename=VERSION
if [ -f "$filename" ]; then
  echo "Arquivo de versão localizado..."
  rm $filename
  echo -n $2 >> $filename
else
  echo "O arquivo de versão não existe!"
  exit 1;
fi;

echo "Sucesso ao atualizar a versão. Atualize os arquivos no repositório."
