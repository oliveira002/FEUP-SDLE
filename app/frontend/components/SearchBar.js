import React, { useState } from 'react';
import { View, TextInput, TouchableOpacity, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';


const SearchBar = ({ onSearch }) => {
    const [searchTerm, setSearchTerm] = useState('');
  
    const handleSearch = () => {
      onSearch(searchTerm);
    };
  
    return (
      <View style={styles.container}>
        <TextInput
          style={styles.input}
          placeholder="Search..."
          value={searchTerm}
          onChangeText={(text) => setSearchTerm(text)}
          underlineColorAndroid="transparent"
           // Add this line to remove the border
        />
        <TouchableOpacity onPress={handleSearch}>
          <Ionicons name="md-search" size={24} color="black" />
        </TouchableOpacity>
      </View>
    );
  };
  
  const styles = StyleSheet.create({
    container: {
      flexDirection: 'row',
      alignItems: 'center',
      backgroundColor: 'lightgray', // Optional: add a background color
      borderRadius: 5,
      padding: 8,
      width: 300
    },
    input: {
      flex: 1,
      marginRight: 8,
      outlineStyle: 'none',
      borderWidth: 0, // Remove the border
    },
  });
  
  export default SearchBar;