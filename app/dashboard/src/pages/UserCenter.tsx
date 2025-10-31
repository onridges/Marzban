import React, { useEffect, useState } from 'react';
import {
  Box,
  VStack,
  Heading,
  Text,
  Stat,
  StatLabel,
  StatNumber,
  StatGroup,
  Progress,
  Button,
  useToast,
  Card,
  CardBody,
  SimpleGrid,
  Badge,
  HStack,
  IconButton,
  Tooltip,
  useClipboard,
  Flex,
  Tag,
  TagLabel,
  chakra,
  useColorMode,
} from '@chakra-ui/react';
import { QRCodeCanvas } from 'qrcode.react';
import { useAuth } from '../contexts/AuthContext';
import { getAuthToken } from '../utils/authStorage';
import { fetch } from '../service/http';
import { ClipboardIcon, ArrowLeftOnRectangleIcon, MoonIcon, SunIcon } from '@heroicons/react/24/outline';
import { useNavigate } from 'react-router-dom';
import { Footer } from 'components/Footer';
import { useTranslation } from 'react-i18next';
import { Language } from 'components/Language';
import { updateThemeColor } from 'utils/themeColor';

export function UserCenter() {
  const { user, isAuthenticated, logout } = useAuth();
  const { t } = useTranslation();
  const navigate = useNavigate();
  const toast = useToast();
  const [userData, setUserData] = useState<any>(null);
  const [subscriptions, setSubscriptions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [subscriptionUrl, setSubscriptionUrl] = useState<string | null>(null);
  const { onCopy, setValue } = useClipboard("");
  const LogoutIcon = chakra(ArrowLeftOnRectangleIcon);
  const iconProps = { baseStyle: { w: 4, h: 4 } } as const;
  const DarkIcon = chakra(MoonIcon, iconProps);
  const LightIcon = chakra(SunIcon, iconProps);
  const { colorMode, toggleColorMode } = useColorMode();

  useEffect(() => {
    // 未登录直接跳回登录页
    const token = getAuthToken();
    // 仅以 token 是否存在为准，避免首次登录时 isAuthenticated 状态更新的竞态问题
    if (!token) {
      navigate('/login');
      return;
    }

    const controller = new AbortController();
    const { signal } = controller;
    const isAbortError = (err: any) => err?.name === 'AbortError' || err?.code === 20 || err?.message?.includes('aborted');

    const fetchUserData = async () => {
      try {
        setLoading(true);

        // 优先使用用户信息（数据库）
        try {
          const me = await fetch('/user/me', { signal });
          const normalized = {
            data_limit: typeof me?.data_limit === 'number' ? me.data_limit : null,
            used_traffic: typeof me?.used_traffic === 'number' ? me.used_traffic : 0,
            expire: typeof me?.expire === 'number' ? me.expire : null,
          };
          setUserData(normalized);
        } catch (e: any) {
          if (isAbortError(e)) return;
          // 后备：订阅信息（计费模块）
          try {
            const data = await fetch('/billing/subscription', { signal });
            const toBytesFromGB = (gb: number | null | undefined) =>
              typeof gb === 'number' ? gb * 1024 * 1024 * 1024 : 0;
            const fallback = {
              data_limit: toBytesFromGB(data?.data_limit_gb ?? 0),
              used_traffic: toBytesFromGB(data?.data_used_gb ?? 0),
              expire: data?.end_date ? Math.floor(new Date(data.end_date).getTime() / 1000) : null,
            };
            setUserData(fallback);
          } catch (e2: any) {
            if (isAbortError(e2)) return;
            // 双重失败则优雅降级为不限/0
            setUserData({ data_limit: null, used_traffic: 0, expire: null });
          }
        }

        // 订阅链接（用户中心）
        try {
          const sub = await fetch('/user/subscription', { signal });
          if (sub?.subscription_url) {
            setSubscriptionUrl(String(sub.subscription_url));
          } else {
            setSubscriptionUrl(null);
          }
        } catch (e3: any) {
          if (isAbortError(e3)) return;
          setSubscriptionUrl(null);
        }

        // 我的订单
        try {
          const orders = await fetch('/billing/orders', { signal });
          setSubscriptions(Array.isArray(orders) ? orders : []);
        } catch (e4: any) {
          if (isAbortError(e4)) return;
          setSubscriptions([]);
        }

      } catch (error) {
        if (isAbortError(error)) return;
        console.error('Failed to fetch user data:', error);
        toast({
          title: '获取数据失败',
          description: '无法加载用户数据，请稍后重试',
          status: 'error',
          duration: 5000,
          isClosable: true,
        });
      } finally {
        if (!signal.aborted) setLoading(false);
      }
    };

    fetchUserData();

    return () => {
      controller.abort();
    };
  }, [toast, isAuthenticated, navigate]);

  const handleCopySubscription = (link: string) => {
    setValue(link);
    onCopy();
    toast({
      title: t('userCenter.copy.successTitle'),
      description: t('userCenter.copy.successDesc'),
      status: 'success',
      duration: 2000,
      isClosable: true,
    });
  };

  const formatBytes = (bytes: number) => {
    if (!bytes) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  // 管理员页面有统一的头部菜单（含退出登录），此处无需重复按钮

  return (
    <VStack justifyContent="space-between" minH="100vh" p="6" rowGap={4}>
      <Box w="full">
        {/* 轻量级用户页顶部栏，避免触发 /api/admin 调用 */}
        <HStack justifyContent="space-between" alignItems="center" w="full" pb={2} borderBottomWidth="1px" borderColor="gray.200" _dark={{ borderColor: 'gray.700' }}>
          <Text as="h1" fontWeight="semibold" fontSize="2xl">{t('userCenter.title')}</Text>
          <HStack>
            <Language />
            <IconButton
              size="sm"
              variant="outline"
              aria-label="switch theme"
              onClick={() => {
                updateThemeColor(colorMode == "dark" ? "light" : "dark");
                toggleColorMode();
              }}
            >
              {colorMode === "light" ? <DarkIcon /> : <LightIcon />}
            </IconButton>
            <Button
              size="sm"
              variant="outline"
              leftIcon={<LogoutIcon w={{ base: 4, md: 5 }} h={{ base: 4, md: 5 }} />}
              onClick={async () => {
                try {
                  await logout();
                } finally {
                  navigate('/login');
                }
              }}
            >
              {t('header.logout')}
            </Button>
          </HStack>
        </HStack>
        <Box mt="4">
          <Text color="gray.600" _dark={{ color: 'gray.400' }}>
            {t('userCenter.welcome', { username: user?.username })}
          </Text>
        </Box>

        {/* 第三行开始：三个方块，风格与管理员界面一致 */}
        <SimpleGrid columns={{ base: 1, md: 3 }} spacing={4}>
          {/* 订阅链接 */}
          <Card
            borderWidth="1px"
            borderColor="light-border"
            bg="#F9FAFB"
            _dark={{ borderColor: "gray.600", bg: "gray.750" }}
            borderStyle="solid"
            boxShadow="none"
            borderRadius="12px"
          >
            <CardBody p={6}>
              <Heading size="md" fontWeight="semibold" mb={4}>
                {t('userCenter.subscription.title')}
              </Heading>
              {subscriptionUrl ? (
                <VStack align="stretch" spacing={4}>
                  <Box display="flex" justifyContent="center">
                    <QRCodeCanvas
                      size={140}
                      value={String(subscriptionUrl).startsWith('/') ? `${window.location.origin}${subscriptionUrl}` : String(subscriptionUrl)}
                      includeMargin={false}
                      level={"L"}
                      bgColor="white"
                    />
                  </Box>
                  <Box as="span" noOfLines={1} title={subscriptionUrl} textAlign="center" color="gray.600" _dark={{ color: 'gray.400' }} display="block">
                    {subscriptionUrl}
                  </Box>
                  <HStack justifyContent="center" spacing={3}>
                    <Button
                      onClick={() => handleCopySubscription(subscriptionUrl)}
                      variant="outline"
                      colorScheme="primary"
                      size="sm"
                    >
                      {t('userCenter.subscription.copyLink')}
                    </Button>
                    <Button
                      onClick={() => navigate('/user/payment')}
                      colorScheme="blue"
                      size="sm"
                    >
                      {t('userCenter.subscription.pay')}
                    </Button>
                  </HStack>
                </VStack>
              ) : (
                <Text color="gray.500">{t('userCenter.subscription.none')}</Text>
              )}
            </CardBody>
          </Card>

          {/* 用量统计 */}
          <Card
            borderWidth="1px"
            borderColor="light-border"
            bg="#F9FAFB"
            _dark={{ borderColor: "gray.600", bg: "gray.750" }}
            borderStyle="solid"
            boxShadow="none"
            borderRadius="12px"
          >
            <CardBody p={6}>
              <Heading size="md" fontWeight="semibold" mb={4}>
                {t('userCenter.usage.title')}
              </Heading>
              <StatGroup>
                <Stat>
                  <StatLabel>{t('userCenter.usage.total')}</StatLabel>
                  <StatNumber>{userData?.data_limit ? formatBytes(userData.data_limit) : t('userCenter.usage.unlimited')}</StatNumber>
                </Stat>
              <Stat>
                <StatLabel>{t('userCenter.usage.used')}</StatLabel>
                <StatNumber>{userData?.used_traffic ? formatBytes(userData.used_traffic) : '0 B'}</StatNumber>
              </Stat>
              <Box w="full" pt={2}>
                {userData?.data_limit ? (
                  <Progress value={Math.min(100, Math.floor(((userData.used_traffic || 0) / userData.data_limit) * 100))} size="sm" borderRadius="md" colorScheme="primary" />
                ) : (
                  <Progress isIndeterminate size="sm" borderRadius="md" colorScheme="gray" />
                )}
              </Box>
              <Stat>
                <StatLabel>{t('userCenter.usage.remaining')}</StatLabel>
                <StatNumber>
                  {userData?.data_limit
                    ? formatBytes(Math.max(0, userData.data_limit - (userData.used_traffic || 0)))
                    : t('userCenter.usage.unlimited')}
                </StatNumber>
              </Stat>
                <Stat>
                  <StatLabel>{t('userCenter.usage.expire')}</StatLabel>
                  <StatNumber>{userData?.expire ? new Date(userData.expire * 1000).toLocaleDateString() : t('userCenter.usage.permanent')}</StatNumber>
                </Stat>
              </StatGroup>
            </CardBody>
          </Card>

          {/* 套餐订单 */}
          <Card
            borderWidth="1px"
            borderColor="light-border"
            bg="#F9FAFB"
            _dark={{ borderColor: "gray.600", bg: "gray.750" }}
            borderStyle="solid"
            boxShadow="none"
            borderRadius="12px"
          >
            <CardBody p={6}>
              <Heading size="md" fontWeight="semibold" mb={4}>
                {t('userCenter.orders.title')}
              </Heading>
              {subscriptions.length > 0 ? (
                <VStack spacing={3} align="stretch">
                  {subscriptions.slice(0, 3).map((order: any, index: number) => (
                    <HStack key={index} justifyContent="space-between">
                      <VStack align="start" spacing={0}>
                        <Text fontWeight="semibold">#{order.id}</Text>
                        <Text fontSize="sm" color="gray.600">{t('userCenter.orders.planId')}: {order.plan_id}</Text>
                        <Text fontSize="sm" color="gray.500">{t('userCenter.orders.createdAt')}: {order.created_at ? new Date(order.created_at).toLocaleString() : '-'}</Text>
                      </VStack>
                      <VStack align="end" spacing={0}>
                        <Badge colorScheme={order.status === 'paid' ? 'green' : order.status === 'pending' ? 'yellow' : 'red'}>
                          {order.status}
                        </Badge>
                        <Text>{t('userCenter.orders.amount')}: ¥{order.amount}</Text>
                      </VStack>
                    </HStack>
                  ))}
                  <HStack justifyContent="flex-end">
                    <Button size="sm" variant="outline" colorScheme="primary" onClick={() => navigate('/user/orders')}>
                      {t('userCenter.orders.viewAll')}
                    </Button>
                  </HStack>
                </VStack>
              ) : (
                <Text color="gray.500">{t('userCenter.orders.none')}</Text>
              )}
            </CardBody>
          </Card>
        </SimpleGrid>
      </Box>
      <Footer />
    </VStack>
  );
}
