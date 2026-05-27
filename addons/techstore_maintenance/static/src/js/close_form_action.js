/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { FormController } from "@web/views/form/form_controller";

patch(FormController.prototype, {
  async beforeExecuteActionButton(clickParams) {
    if (clickParams.name === "action_cancelar_creacion") {
      await this.discard();
      return false;
    }
    return super.beforeExecuteActionButton(...arguments);
  },
});
