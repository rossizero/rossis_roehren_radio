cd ansible 
rm -r roles/spotifyd
ansible-galaxy install -r requirements.yml -p roles/
ansible-playbook site.yml