import React, { useState } from "react";
import { useNavigate } from 'react-router-dom'
import Button from '@mui/material/Button';
import Box from '@mui/material/Box';
import TextField from '@mui/material/TextField';
import AddShoppingCartIcon from '@mui/icons-material/AddShoppingCart';
const Home = () => {
;
    const [shoppingListId, setShoppingListId] = useState('');
    const navigate = useNavigate();
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
        <h1>Welcome to Shopping Lists!</h1>
        

        <Button className="home-button" onClick={handleNewList} variant="contained">Create New Shopping List</Button>
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
