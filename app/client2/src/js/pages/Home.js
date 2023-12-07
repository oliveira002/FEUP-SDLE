import React, { useState, useEffect} from "react";
import { useNavigate } from 'react-router-dom'
import Button from '@mui/material/Button';
import Box from '@mui/material/Box';
import TextField from '@mui/material/TextField';
import AddShoppingCartIcon from '@mui/icons-material/AddShoppingCart';
import { fetchShoppingLists } from "../shoppingListOperations";
import ButtonGroup from '@mui/material/ButtonGroup';


const Home = () => {

    const { ipcRenderer } = window.require('electron');

    ipcRenderer.send('frontMessage', {body: "shopping_list_1", type: "GET"});

    // Listen for the response from the main process
    ipcRenderer.on('zmqMessage', (event, information) => {
        console.log(JSON.stringify(information))
    // Do something with the information in your React component
    });

    
    const userid = 1;
    console.log("id", userid);
    const [shoppingListId, setShoppingListId] = useState('');
    const [shoppingLists, setShoppingLists] = useState(null);
    if(shoppingLists){ 
        shoppingLists.ShoppingLists.map((shoppingList) => {
            console.log("shoppingList", shoppingList);
        })
      
    }

    const navigate = useNavigate();

    useEffect(() => {
        const fetchData = async () => {
            try {
                const data = await fetchShoppingLists(userid);
                setShoppingLists(data);
                                   
               
            } catch (error) {
                // Handle errors or display a message to the user
            }
        };

        ipcRenderer.send('getInformation', 'some data');
  
        fetchData();
    }, []);

  
    const handleNewList = () => {

        // Generate a new ID (for example, a random number for simplicity)
        const newId = Math.floor(Math.random() * 1000); // Generate a random number (replace this with your logic for generating IDs)
        
        // Redirect to the new list URL
        setShoppingListId(newId);
        console.log("newId", newId);
        // Navigate to the new list URL
        navigate(`/shopping-list/${newId}`);
        
        
    };

    const handleShopingList = () => {
        console.log("shoppingListId", shoppingListId);
        navigate(`/shopping-list/${shoppingListId}`);
    }


    return (
        <div>
        <AddShoppingCartIcon sx={{ fontSize: 40 }}/>
        <h1>Welcome!</h1>
        <div className="shopping-lists home-button">
            <h3 >My Shopping Lists</h3>
            <ButtonGroup
                orientation="vertical"
                aria-label="vertical outlined button group"
            >
            {shoppingLists && shoppingLists.ShoppingLists.map((shoppingList) => {
                return (
                    
                        <Button key={shoppingList.uuid} onClick={() => navigate(`/shopping-list/${shoppingList.uuid}`)}>Shopping List ID: {shoppingList.uuid}</Button>
                      
                );

            }
            )}
            </ButtonGroup>
        </div>

        <Button className="home-button" onClick={handleNewList} variant="contained">Create New Shopping List</Button>
        <div className="shopping-lists">
        </div>
        
        <div className="shopping-row">
            <Box
                component="form"
                sx={{
                    '& .MuiTextField-root': { m: 1, width: '20ch' },
                }}
                noValidate
                autoComplete="off"
                >
                <div>
                    <TextField
                    type="text"
                    placeholder="Enter Shopping List ID"
                    value={shoppingListId}
                    onChange={(e) => setShoppingListId(e.target.value)}
                    
                    />
                
                </div>
                
            </Box>
            <div className="d-flex d-column justify-content-center align-items-center">
                <Button className="home-button"  variant="contained" onClick={handleShopingList} >
                    Enter Shopping List
                </Button>
            </div>
                
            </div>
        </div>
    );
};

export default Home;
