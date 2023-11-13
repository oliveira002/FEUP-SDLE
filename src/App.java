import client.Client;

import java.io.IOException;

public class App {

    public static void main(String[] args) throws IOException {



        for(int i = 1; i <= 1 + 100; i++){
            System.out.println(i);
            Client client = new Client();
            client.start();
            System.out.println();
        }

        while(true){

        }
    }
}
