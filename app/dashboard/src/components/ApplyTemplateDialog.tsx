import { useEffect, useState } from "react";
import {
  Button,
  Checkbox,
  HStack,
  Modal,
  ModalBody,
  ModalCloseButton,
  ModalContent,
  ModalFooter,
  ModalHeader,
  ModalOverlay,
  Select,
  Text,
  VStack,
} from "@chakra-ui/react";
import { useDashboard } from "contexts/DashboardContext";
import { fetch } from "service/http";

type TemplateItem = {
  id: number;
  name: string;
};

export const ApplyTemplateDialog = () => {
  const {
    isApplyingTemplate,
    onApplyingTemplate,
    applyTemplateBulk,
    selectedUsernames,
  } = useDashboard();

  const [templates, setTemplates] = useState<TemplateItem[]>([]);
  const [templateId, setTemplateId] = useState<number | null>(null);
  const [applyInbounds, setApplyInbounds] = useState(true);
  const [applyDataLimit, setApplyDataLimit] = useState(true);
  const [applyExpireDuration, setApplyExpireDuration] = useState(true);

  useEffect(() => {
    if (isApplyingTemplate) {
      fetch("/user_template").then((list: any[]) => {
        const items = (list || []).map((t) => ({ id: t.id, name: t.name }));
        setTemplates(items);
        if (items.length > 0) setTemplateId(items[0].id);
      });
    }
  }, [isApplyingTemplate]);

  const onClose = () => onApplyingTemplate(false);

  const onConfirm = async () => {
    if (!templateId) return;
    await applyTemplateBulk({
      template_id: templateId,
      apply_inbounds: applyInbounds,
      apply_data_limit: applyDataLimit,
      apply_expire_duration: applyExpireDuration,
    });
  };

  return (
    <Modal isOpen={isApplyingTemplate} onClose={onClose} isCentered>
      <ModalOverlay />
      <ModalContent>
        <ModalHeader>批量应用模板</ModalHeader>
        <ModalCloseButton />
        <ModalBody>
          <VStack align="stretch" spacing={4}>
            <HStack justify="space-between">
              <Text>已选择用户数：</Text>
              <Text>{selectedUsernames.length}</Text>
            </HStack>

            <VStack align="stretch">
              <Text>选择模板：</Text>
              <Select
                value={templateId ?? undefined}
                onChange={(e) => setTemplateId(parseInt(e.target.value, 10))}
              >
                {templates.map((tpl) => (
                  <option key={tpl.id} value={tpl.id}>
                    {tpl.name}
                  </option>
                ))}
              </Select>
            </VStack>

            <VStack align="stretch" spacing={2}>
              <Checkbox
                isChecked={applyDataLimit}
                onChange={(e) => setApplyDataLimit(e.target.checked)}
              >
                覆盖流量限制
              </Checkbox>
              <Checkbox
                isChecked={applyExpireDuration}
                onChange={(e) => setApplyExpireDuration(e.target.checked)}
              >
                覆盖过期时间（根据模板时长）
              </Checkbox>
              <Checkbox
                isChecked={applyInbounds}
                onChange={(e) => setApplyInbounds(e.target.checked)}
              >
                覆盖入站（协议与标签）
              </Checkbox>
            </VStack>
          </VStack>
        </ModalBody>
        <ModalFooter>
          <Button mr={3} onClick={onClose} variant="ghost">
            取消
          </Button>
          <Button
            colorScheme="primary"
            onClick={onConfirm}
            isDisabled={!templateId || selectedUsernames.length === 0}
          >
            应用
          </Button>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
};