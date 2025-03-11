#!/bin/bash


cd /opt || exit 1
git clone https://github.com/odem/mps.git
cd mps || exit 2
./all.bash

