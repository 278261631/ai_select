# ai_select

准备： python manager.py collectstatic?
python manager.py create superuser?

nginx

        location /ai_select/ {
            root   html;
            index  index.html index.htm;
			proxy_pass  http://127.0.0.1:18000; 
			proxy_set_header Host $proxy_host; 
			proxy_set_header X-Real-IP $remote_addr;
			proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        }
        location /ai_admin/ {
            root   html;
            index  index.html index.htm;
			proxy_pass  http://127.0.0.1:18000; 
			proxy_set_header Host $proxy_host; 
			proxy_set_header X-Real-IP $remote_addr;
			proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        }
	
        location /ai_static/ {
            root   html;
            index  index.html index.htm;
			proxy_pass  http://127.0.0.1:18000; 
			proxy_set_header Host $proxy_host; 
			proxy_set_header X-Real-IP $remote_addr;
			proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        }


