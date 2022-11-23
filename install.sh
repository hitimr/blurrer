# redirect output to shell
set -x  

pip install -r requirements.txt

# download and extract tensorflow (too big for git)
cd lib 
wget -O tensorflow.tar.gz https://doubango.org/deep_learning/libtensorflow_r1.14_cpu+gpu_linux_x86-64.tar.gz
tar xzfv tensorflow.tar.gz

# compile and install package
pip install .

# cleanup
cd ..
set +x
