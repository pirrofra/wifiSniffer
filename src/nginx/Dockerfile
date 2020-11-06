FROM nginx:alpine

ADD ./config/nginx.conf /etc/nginx/nginx.conf
ADD ./config/default.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
