import React, { useEffect, useState } from 'react';
import { Box, VStack, Heading, Text, Badge, HStack, Card, CardBody, useToast, Button } from '@chakra-ui/react';
import { fetch } from '../service/http';
import { getAuthToken } from '../utils/authStorage';
import { useNavigate } from 'react-router-dom';

export function UserOrders() {
  const [orders, setOrders] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const toast = useToast();
  const navigate = useNavigate();

  useEffect(() => {
    const token = getAuthToken();
    if (!token) {
      navigate('/login');
      return;
    }
    const controller = new AbortController();
    const { signal } = controller;
    const isAbortError = (err: any) => err?.name === 'AbortError' || err?.code === 20 || err?.message?.includes('aborted');
    const load = async () => {
      try {
        setLoading(true);
        const resp = await fetch('/billing/orders', { signal });
        setOrders(Array.isArray(resp) ? resp : []);
      } catch (e: any) {
        if (isAbortError(e)) return;
        setOrders([]);
        toast({ title: '加载订单失败', status: 'error', duration: 3000 });
      } finally {
        if (!signal.aborted) setLoading(false);
      }
    };
    load();
    return () => {
      controller.abort();
    };
  }, [toast, navigate]);

  return (
    <VStack justifyContent="space-between" minH="100vh" p="6" rowGap={4}>
      <Box w="full">
        <HStack justifyContent="space-between" alignItems="center" w="full" pb={2} borderBottomWidth="1px" borderColor="gray.200" _dark={{ borderColor: 'gray.700' }}>
          <Text as="h1" fontWeight="semibold" fontSize="2xl">订单列表</Text>
          <Button size="sm" variant="outline" onClick={() => navigate('/user')}>返回</Button>
        </HStack>
        <Box mt="4">
          <Heading size="md" mb={4}>全部订单</Heading>
          <VStack spacing={4} align="stretch">
            {orders.length > 0 ? (
              orders.map((order: any, index: number) => (
                <Card key={index}>
                  <CardBody>
                    <HStack justifyContent="space-between" width="100%">
                      <VStack align="start" spacing={1}>
                        <Text fontWeight="bold">订单 #{order.id}</Text>
                        <Text fontSize="sm" color="gray.600">计划 ID: {order.plan_id}</Text>
                        <Text fontSize="sm" color="gray.500">创建时间: {order.created_at ? new Date(order.created_at).toLocaleString() : '-'}</Text>
                      </VStack>
                      <VStack align="end" spacing={1}>
                        <Badge colorScheme={order.status === 'paid' ? 'green' : order.status === 'pending' ? 'yellow' : 'red'}>
                          {order.status}
                        </Badge>
                        <Text>金额: ¥{order.amount}</Text>
                      </VStack>
                    </HStack>
                  </CardBody>
                </Card>
              ))
            ) : (
              <Text>暂无订单记录</Text>
            )}
          </VStack>
        </Box>
      </Box>
    </VStack>
  );
}

export default UserOrders;