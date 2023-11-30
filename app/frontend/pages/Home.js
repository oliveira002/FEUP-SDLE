import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import SearchBar from '../components/SearchBar';
import { io } from 'socket.io-client';
import { useEffect } from 'react';


const Home = () => {

    const socket = io.connect('http://localhost:4444', { transports: ['websocket'], cors: { origin: '*' } });

    useEffect(() => {
        socket.on('zmqMessage', (result) => {
            console.log('Received ZeroMQ message:', result);
        });

    }, [socket]);

    const handleSearch = (searchTerm) => {
        socket.emit('frontendMessage', { body: searchTerm, type: 'GET' });
    };


    return (
      <View style={styles.container}>
        <View style={styles.content}>
          <SearchBar onSearch={handleSearch}/>
        </View>
      </View>
    );
  };

const styles = StyleSheet.create({
    container: {
      flex: 1,
    },
    content: {
      flex: 1,
      justifyContent: 'center',
      alignItems: 'center',
    },
    searchContainer: {
      alignItems: 'center',
      padding: 16,
    },
});

export default Home;