tmux new-session -d -s workers
for i in {0..100}
do
	tmux new-window -c "$PWD" rq worker
done
