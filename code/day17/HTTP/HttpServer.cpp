#include "HttpServer.h"
#include "../TCP/Socket.h"
#include "../TCP/Acceptor.h"
#include "../TCP/TcpServer.h"
#include "../TCP/TcpConnection.h"
#include "../TCP/Buffer.h"
#include "HttpResponse.h"
#include "HttpRequest.h"
#include "HttpContext.h"
#include <functional>
#include <iostream>
 
void HttpServer::HttpDefaultCallBack(const HttpRequest& request, HttpResponse *resp){
    resp->SetStatusCode(HttpResponse::HttpStatusCode::k404NotFound);
    resp->SetStatusMessage("Not Found");
    resp->SetCloseConnection(true);
}

HttpServer::HttpServer(const char *ip, const int port)  {
    server_ = std::make_unique<TcpServer>(ip, port);
    server_->set_connection_callback(
        std::bind(&HttpServer::onConnection, this, std::placeholders::_1));

    server_->set_message_callback(
        std::bind(&HttpServer::onMessage, this, std::placeholders::_1)
    );
    SetHttpCallback(std::bind(&HttpServer::HttpDefaultCallBack, this, std::placeholders::_1, std::placeholders::_2));
};

HttpServer::~HttpServer(){
};

void HttpServer::onConnection(const TcpConnectionPtr &conn){
    std::cout << "New connection fd: " << conn->socket()->fd() << std::endl;
}

void HttpServer::onMessage(const TcpConnectionPtr &conn){
    if (conn->state() == TcpConnection::ConnectionState::Connected)
    {
        std::cout << "message from connection fd: " << conn->socket()->fd() << std::endl;
        HttpContext *context = conn->context();
        if (!context->ParaseRequest(conn->read_buf()->c_str(), conn->read_buf()->Size()))
        {
            conn->Send("HTTP/1.1 400 Bad Request\r\n\r\n");
            conn->OnClose();
        }

        if (context->GetCompleteRequest())
        {
            onRequest(conn, *context->request());
            context->ResetContextStatus();
        }
    }
}

void HttpServer::SetHttpCallback(const HttpServer::HttpResponseCallback &cb){
    response_callback_ = std::move(cb);
}

void HttpServer::onRequest(const TcpConnectionPtr &conn, const HttpRequest &request){
    std::string connection_state = request.GetHeader("Connection");
    bool close = (connection_state == "Close" ||
                  request.version() == HttpRequest::Version::kHttp10 &&
                  connection_state != "keep-alive");
    HttpResponse response(close);
    response_callback_(request, &response);

    conn->Send(response.message().c_str());

    if(response.IsCloseConnection()){
        conn->OnClose();
    }
}

void HttpServer::start(){
    server_->Start();
}
