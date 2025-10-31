import React from 'react';
import { Box, VStack, HStack, Heading, Card, CardBody, Button, Text } from '@chakra-ui/react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';

export default function UserPayment() {
  const navigate = useNavigate();
  const { t } = useTranslation();

  return (
    <VStack justifyContent="space-between" minH="100vh" p="6" rowGap={4}>
      <Box w="full">
        <HStack justifyContent="space-between" alignItems="center" w="full" pb={2} borderBottomWidth="1px" borderColor="gray.200" _dark={{ borderColor: 'gray.700' }}>
          <Heading as="h1" fontWeight="semibold" fontSize="2xl">{t('userPayment.title')}</Heading>
          <Button size="sm" variant="outline" onClick={() => navigate('/user')}>{t('previous') || '返回'}</Button>
        </HStack>
        <Box mt="4">
          <Card borderWidth="1px" borderColor="light-border" boxShadow="none" borderRadius="12px" bg="#F9FAFB" _dark={{ borderColor: 'gray.600', bg: 'gray.750' }}>
            <CardBody p={6}>
              <Heading size="md" fontWeight="semibold" mb={4}>{t('userPayment.title')}</Heading>
              <Text color="gray.600" _dark={{ color: 'gray.300' }}>
                {t('userPayment.comingSoon', { defaultValue: '支付页面开发中（功能细节明日完善）' })}
              </Text>
            </CardBody>
          </Card>
        </Box>
      </Box>
    </VStack>
  );
}