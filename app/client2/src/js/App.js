import React from 'react';
import {HashRouter,Route, Routes} from "react-router-dom";
import Home from './pages/Home';
import ShoppingList from './pages/ShoppingList';

const App = ()=> {
  return (
    <HashRouter>
        <Routes>
                <Route path="/" element={<Home/>}/>
                <Route path="/shopping-list/:id" element={<ShoppingList/>}/>
        </Routes>
    </HashRouter>    
  );
}

export default App;