import React, { useEffect, useState } from 'react';
import { Box, VStack, Heading, HStack, Card, CardBody, useToast, Button } from '@chakra-ui/react';
import { QRCodeCanvas } from 'qrcode.react';
import { fetch } from '../service/http';
import { getAuthToken } from '../utils/authStorage';
import { useNavigate } from 'react-router-dom';

export function UserConfig() {
  const [subscriptionUrl, setSubscriptionUrl] = useState<string | null>(null);
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
        const sub = await fetch('/user/subscription', { signal });
        setSubscriptionUrl(sub?.subscription_url ? String(sub.subscription_url) : null);
      } catch (e: any) {
        if (isAbortError(e)) return;
        setSubscriptionUrl(null);
        toast({ title: '加载订阅信息失败', status: 'error', duration: 3000 });
      } finally {
        if (!signal.aborted) setLoading(false);
      }
    };
    load();
    return () => {
      controller.abort();
    }
  }, [toast, navigate]);

  const handleCopy = () => {
    if (!subscriptionUrl) return;
    navigator.clipboard.writeText(subscriptionUrl);
    toast({ title: '已复制订阅链接', status: 'success', duration: 2000 });
  };

  return (
    <VStack justifyContent="space-between" minH="100vh" p="6" rowGap={4}>
      <Box w="full">
        <HStack justifyContent="space-between" alignItems="center" w="full" pb={2} borderBottomWidth="1px" borderColor="gray.200" _dark={{ borderColor: 'gray.700' }}>
          <Heading as="h1" fontWeight="semibold" fontSize="2xl">配置</Heading>
          <Button size="sm" variant="outline" onClick={() => navigate('/user')}>返回</Button>
        </HStack>
        <Box mt="4">
          <Card>
            <CardBody>
              <Heading size="md" mb={4}>订阅与配置</Heading>
              {subscriptionUrl ? (
                <VStack spacing={4}>
                  <QRCodeCanvas
                    size={180}
                    value={String(subscriptionUrl).startsWith('/') ? `${window.location.origin}${subscriptionUrl}` : String(subscriptionUrl)}
                    includeMargin={false}
                    level={"L"}
                    bgColor="white"
                  />
                  <Box as="span" noOfLines={1} title={subscriptionUrl} textAlign="center" color="gray.600" _dark={{ color: 'gray.400' }} display="block">
                    {subscriptionUrl}
                  </Box>
                  <HStack>
                    <Button onClick={handleCopy} variant="outline" colorScheme="primary" size="sm">拷贝订阅链接</Button>
                    <Button as="a" href={String(subscriptionUrl).startsWith('/') ? `${window.location.origin}${subscriptionUrl}` : subscriptionUrl} target="_blank" rel="noopener noreferrer" colorScheme="blue" size="sm">打开</Button>
                  </HStack>
                  <VStack spacing={1} align="start" w="full" pt={2}>
                    <Box as="span" fontSize="sm" color="gray.600">提示：可在常见客户端中直接扫描二维码或粘贴订阅链接以完成配置。</Box>
                  </VStack>
                </VStack>
              ) : (
                <Box as="span">暂无订阅信息</Box>
              )}
            </CardBody>
          </Card>
        </Box>
      </Box>
    </VStack>
  );
}

export default UserConfig;