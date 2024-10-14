#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/unistd.h>
#include <sys/types.h>
#include <sys/errno.h>
#include <netinet/in.h>
#include <signal.h>
#include <sys/stat.h>
#include <sys/epoll.h>
#include <set>
#include <ctime>

using namespace std;

#define BUFFSIZE 2048
#define DEFAULT_PORT 11451
#define MAXLINK 64
#define CMDLEN 2

int sockfd; // The socket fd of server.
set<int> connfds; // The fds of connected clients.
int connum; // The number of connected clients.

void stopServerRunning(int p)
{
	close(sockfd);
	printf("\nClose Server.\n");
	exit(0);
}

int main()
{
	setbuf(stdout, NULL);
	struct sockaddr_in servaddr;
	char buff[BUFFSIZE];

	time_t nowtime;
	time(&nowtime);
	tm* p = localtime(&nowtime);
	printf("%04d/%02d/%02d-%02d:%02d:%02d\n", p->tm_year + 1900, p->tm_mon + 1, p->tm_mday, p->tm_hour, p->tm_min, p->tm_sec);

	sockfd = socket(AF_INET, SOCK_STREAM, 0);
	if (-1 == sockfd){
		printf("Create socket failed(%d): %s\n", errno, strerror(errno));
		return -1;
	}

	bzero(&servaddr, sizeof(servaddr));
	servaddr.sin_family = AF_INET;
	servaddr.sin_addr.s_addr = htonl(INADDR_ANY);
	servaddr.sin_port = htons(DEFAULT_PORT);
	if (-1 == bind(sockfd, (struct sockaddr*)&servaddr, sizeof(servaddr))){
		printf("Bind error(%d): %s\n", errno, strerror(errno));
		return -1;
	}

	if (-1 == listen(sockfd, MAXLINK)){
		printf("Listen error(%d): %s\n", errno, strerror(errno));
		return -1;
	}

	printf("Listening...\n");

	int epfd = epoll_create(100);
	if (epfd == -1){
		printf("Create epoll error(%d): %s\n", errno, strerror(errno));
		return -1;
	}

	struct epoll_event ev;
	ev.events = EPOLLIN;
	ev.data.fd = sockfd;
	if (-1 == epoll_ctl(epfd, EPOLL_CTL_ADD, sockfd, &ev)){
		printf("Epoll_clt error(%d): %s\n", errno, strerror(errno));
		return -1;
	}

	struct epoll_event evs[MAXLINK+1];
	int size = sizeof(evs) / sizeof(struct epoll_event);

	while(1){
		signal(SIGINT, stopServerRunning);

		int num = epoll_wait(epfd, evs, size, -1);
		//printf("get event.\n");
		for (int i = 0; i < num; i++){
			int curfd = evs[i].data.fd;
			
			if (curfd == sockfd){
				time(&nowtime);
				tm* p = localtime(&nowtime);
				printf("%04d/%02d/%02d-%02d:%02d:%02d\n", p->tm_year + 1900, p->tm_mon + 1, p->tm_mday, p->tm_hour, p->tm_min, p->tm_sec);

				int cfd = accept(curfd, NULL, NULL);
				connfds.insert(cfd);
				
				ev.events = EPOLLIN;
				ev.data.fd = cfd;
				int ret =  epoll_ctl(epfd, EPOLL_CTL_ADD, cfd, &ev);
				if (-1 == ret){
					printf("Epoll_clt error(%d): %s\n", errno, strerror(errno));
					return -1;
				}
				printf("New connect(%lu).\n", connfds.size());
			}
			else{
				time(&nowtime);
				tm* p = localtime(&nowtime);
				printf("%04d/%02d/%02d-%02d:%02d:%02d\n", p->tm_year + 1900, p->tm_mon + 1, p->tm_mday, p->tm_hour, p->tm_min, p->tm_sec);

				bzero(buff, BUFFSIZE);

				int len = recv(curfd, buff, sizeof(buff), 0);

				if (len == 0){
					epoll_ctl(epfd, EPOLL_CTL_DEL, curfd, NULL);
					connfds.erase(curfd);
					close(curfd);
					printf("One disconnect(%lu).\n", connfds.size());
				}
				else if(len > 0){
				//	printf("Recv %d: %s\n", len, buff);	
					for (int f : connfds){
						if (f == curfd) continue;
						int slen = send(f, buff, len, MSG_NOSIGNAL);
					}
				}
				else{
					printf("Recv error(%d): %s\n", errno, strerror(errno));
					epoll_ctl(epfd, EPOLL_CTL_DEL, curfd, NULL);
					connfds.erase(curfd);
					close(curfd);
					printf("One disconnect(%lu).\n", connfds.size());
				}
			}
		}
	}
}

