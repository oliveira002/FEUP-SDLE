package client;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;
import java.util.concurrent.CompletableFuture;

public class Client {

    public void start() {
        CompletableFuture.runAsync(() -> {
            try {
                // Define the URL of the server endpoint
                String serverUrl = "http://localhost:8080/hello";

                // Create a URL object
                URL url = new URL(serverUrl);

                // Open a connection to the URL
                HttpURLConnection connection = (HttpURLConnection) url.openConnection();

                // Set the request method to GET
                connection.setRequestMethod("GET");

                // Get the response code
                int responseCode = connection.getResponseCode();
                //System.out.println("Response Code: " + responseCode);

                // Read the response from the server
                try (BufferedReader reader = new BufferedReader(new InputStreamReader(connection.getInputStream()))) {
                    String line;
                    StringBuilder response = new StringBuilder();

                    while ((line = reader.readLine()) != null) {
                        response.append(line);
                    }

                    // Print the JSON response
                    System.out.println(/*"Response from server:\n" + */response.toString());
                } finally {
                    // Close the connection
                    connection.disconnect();
                }
            } catch (IOException e) {
                e.printStackTrace();
            }
        });
    }
}

