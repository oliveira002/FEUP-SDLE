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



