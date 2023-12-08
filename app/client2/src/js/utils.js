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
                throw new Error("User not found!");
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

