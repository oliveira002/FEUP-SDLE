package server;

import com.sun.net.httpserver.HttpServer;
import com.sun.net.httpserver.HttpHandler;
import com.sun.net.httpserver.HttpExchange;

import java.io.IOException;
import java.io.OutputStream;
import java.net.InetSocketAddress;
import java.util.concurrent.*;

public class Server {

    static int i = 0;

    private static final Object iLock = new Object();

    public static void main(String[] args) throws IOException {

        int port = 8080;

        // Create an HTTP server that listens on port 8080
        HttpServer server = HttpServer.create(new InetSocketAddress(port), 0);

        // Set the executor to a custom executor with a thread pool
        Executor executor = Executors.newCachedThreadPool();
        server.setExecutor(executor);

        // Create a context for the "/hello" route
        server.createContext("/hello", new HelloHandler());

        // Start the server
        server.start();

        System.out.println("Server is listening on port "+port);
    }

    static class HelloHandler implements HttpHandler {
        @Override
        public void handle(HttpExchange exchange) throws IOException {

            // Handle the request asynchronously
            CompletableFuture.runAsync(() -> {

                // Print a message to the console when a client connects
                System.out.println("Received a connection from: " + exchange.getRemoteAddress());

                try {
                    // Simulate some time-consuming task
                    Thread.sleep(1000);

                    // Send a response
                    String response;
                    synchronized (iLock){
                        response = i + " - Hello";
                        i++;
                    }
                    exchange.sendResponseHeaders(200, response.length());

                    try (OutputStream os = exchange.getResponseBody()) {
                        os.write(response.getBytes());
                        os.close();
                        System.out.println("Connection closed for: " + exchange.getRemoteAddress());
                    }
                } catch (IOException | InterruptedException e) {
                    e.printStackTrace();
                }
            });

            /*
            // Print a message to the console when a client connects
            System.out.println("Received a connection from: " + exchange.getRemoteAddress());

            // Set the response headers
            exchange.getResponseHeaders().set("Content-Type", "application/json");
            exchange.sendResponseHeaders(200, 0);

            // Get the output stream to write the response body
            OutputStream os = exchange.getResponseBody();

            // Write the JSON response
            String response = "{\"message\": \"Hello, World!\"}";
            os.write(response.getBytes());

            // Close the output stream and end the exchange
            os.close();

            // Print a message to the console when a client disconnects
            System.out.println("Connection closed for: " + exchange.getRemoteAddress());*/
        }
    }
}