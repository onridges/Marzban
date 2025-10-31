import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import {
  Box,
  Button,
  FormControl,
  FormLabel,
  Input,
  VStack,
  useToast,
  Heading,
  Text,
  Link,
} from '@chakra-ui/react';

export function Register() {
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const { register } = useAuth();
  const toast = useToast();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (password !== confirmPassword) {
      toast({
        title: '密码不匹配',
        description: '请确保两次输入的密码相同',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
      return;
    }
    
    setIsLoading(true);
    try {
      await register(username, email, password);
      toast({
        title: '注册成功',
        description: '您已成功注册，请登录',
        status: 'success',
        duration: 5000,
        isClosable: true,
      });
      // 注册成功后跳转到登录页
      window.location.href = '#/login';
    } catch (error: any) {
      toast({
        title: '注册失败',
        description: error.message || '请稍后重试',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Box maxW="md" mx="auto" mt={8}>
      <VStack spacing={4} align="stretch">
        <Heading size="lg" textAlign="center">注册</Heading>
        <form onSubmit={handleSubmit}>
          <VStack spacing={4}>
            <FormControl isRequired>
              <FormLabel>用户名</FormLabel>
              <Input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="请输入用户名"
              />
            </FormControl>
            <FormControl isRequired>
              <FormLabel>邮箱</FormLabel>
              <Input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="请输入邮箱"
              />
            </FormControl>
            <FormControl isRequired>
              <FormLabel>密码</FormLabel>
              <Input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="请输入密码"
              />
            </FormControl>
            <FormControl isRequired>
              <FormLabel>确认密码</FormLabel>
              <Input
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="请再次输入密码"
              />
            </FormControl>
            <Button
              type="submit"
              colorScheme="blue"
              width="full"
              isLoading={isLoading}
            >
              注册
            </Button>
          </VStack>
        </form>
        <Text textAlign="center">
          已有账号？
          <Link href="#/login" color="blue.500">
            登录
          </Link>
        </Text>
      </VStack>
    </Box>
  );
}