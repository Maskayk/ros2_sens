git add .
git commit -m "add parser in ros2"
git push
ls -la ~/.ssh
ssh -T git@github.com
sudo ls -la ~/.ssh
ssh -T git@github.com
ssh-keygen -t ed25519 -C "your_email@example.com"
cat ~/.ssh/id_ed25519.pub
ssh -T git@github.com
git push
git add README.md
git commit -m "Add repository README"
git push
source install/setup.bash 
ros2 run sens_analytics stl_analyzer_node 
exit
ros2 service call /sens/parse_code sens_interfaces/srv/ParseStl "{stl_content: 'A I0.0; AN I0.1; = Q0.0;'}"
colcon build --symlink-install
source install/setup.bash 
ros2 service call /sens/parse_code sens_interfaces/srv/ParseStl "{stl_content: 'A I0.0; AN I0.1; = Q0.0;'}"
ros2 interface show sens_interfaces/srv/ParseStl
ros2 service call /sens/parse_code sens_interfaces/srv/ParseStl "{stl_code_text: 'A I0.0; AN I0.1; = Q0.0;'}"
git add .
git add .gitignore 
git commit -m "implement stl analysis ros2 service with pdg filtering"
git push
