const fs = require('fs');
const fileName = './db/users.json';

const { v4: uuidv4 } = require('uuid');

export const fetchShoppingLists = async (userId) => {
    try {
        const response = await fetch(`./db/${userId}/shoppinglists.json`);
        if (response.ok) {
            return await response.json();
        } else {
            throw new Error("Local database file not found!");
        }
    } catch (error) {
        console.error("Error fetching data:", error);
        throw error;
    }
};

export const checkLogin = async (username) => {
    try{
        const response = await fetch(`./db/users.json`);
        if (response.ok) {
            let users = await response.json();
            console.log(users.users)
            let user = users.users.find(user => user.username === username);
            if (user) {
                return user;
            } else {
                // Create new user
                let newUser = {
                    username: username,
                    id: String(uuidv4()),
                }
                users.users.push(newUser);
                fs.writeFile(fileName, JSON.stringify(users), function writeJSON(err) {
                    if (err) return console.log(err);
                    console.log(JSON.stringify(users));
                    console.log('writing to ' + fileName);
                });
                // create a new file and folder for the user

                fs.mkdir(`./db/${newUser.id}`, { recursive: true }, (err) => {

                    if (err) {
                        return console.error(err);
                    }
                    console.log('Directory created successfully!');

                });
               
                fs.writeFile(`./db/${newUser.id}/shoppinglists.json`, JSON.stringify({"ShoppingLists": []}), function writeJSON(err) {
                    if (err) return console.log(err);
                    console.log(JSON.stringify(users));
                    console.log('writing to ' + fileName);
                });


            }
        } else {
            throw new Error("Local database file not found!");
        }
    }
    catch (error) {
        console.error("Error fetching data:", error);
        throw error;
    }
  }


  export const saveShoppingList = async (userId, shoppingListId, shoppingList) => {
    try {
        const filePath = `./db/${userId}/shoppinglists.json`;
        const existingData = fs.readFileSync(filePath, 'utf-8');
        const parsedData = JSON.parse(existingData);

        console.log("Existing Data", parsedData)
        
        // Find the index of the shopping list based on its ID
        const index = parsedData.ShoppingLists.findIndex(list => list.uuid === shoppingListId);
        
        if (index !== -1) {
            // Update the existing shopping list
            parsedData.ShoppingLists[index] = shoppingList;
        } else {
            // Add a new shopping list
            parsedData.ShoppingLists.push(shoppingList);
        }

        console.log("Parsed Data", parsedData)

        // Write the updated data back to the file
        fs.writeFileSync(filePath, JSON.stringify(parsedData, null, 2), 'utf-8');
        console.log('Shopping list saved successfully!');
    } catch (error) {
        console.error('Error saving shopping list:', error);
        throw error;
    }
};