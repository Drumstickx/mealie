import { useAsync, ref, reactive, Ref } from "@nuxtjs/composition-api";
import { useAsyncKey } from "../use-utils";
import { useUserApi } from "~/composables/api";
import { VForm } from "~/types/vuetify";
import { IngredientFood } from "~/types/api-types/recipe";

let foodStore: Ref<IngredientFood[] | null> | null = null;

export const useFoods = function () {
  const api = useUserApi();
  const loading = ref(false);
  const deleteTargetId = ref(0);
  const validForm = ref(true);

  const workingFoodData = reactive<IngredientFood>({
    id: "",
    name: "",
    description: "",
    labelId: undefined,
  });

  const actions = {
    getAll() {
      loading.value = true;
      const units = useAsync(async () => {
        const { data } = await api.foods.getAll();
        return data;
      }, useAsyncKey());

      loading.value = false;
      return units;
    },
    async refreshAll() {
      loading.value = true;
      const { data } = await api.foods.getAll();

      if (data && foodStore) {
        foodStore.value = data;
      }

      loading.value = false;
    },
    async createOne(domForm: VForm | null = null) {
      if (domForm && !domForm.validate()) {
        validForm.value = false;
        return;
      }

      loading.value = true;
      const { data } = await api.foods.createOne(workingFoodData);
      if (data && foodStore?.value) {
        foodStore.value.push(data);
        return data;
      } else {
        this.refreshAll();
      }
      domForm?.reset();
      validForm.value = true;
      this.resetWorking();
      loading.value = false;
    },
    async updateOne() {
      if (!workingFoodData.id) {
        return;
      }

      loading.value = true;
      console.log(workingFoodData);
      const { data } = await api.foods.updateOne(workingFoodData.id, workingFoodData);
      if (data && foodStore?.value) {
        this.refreshAll();
      }
      loading.value = false;
    },
    async deleteOne(id: string | number) {
      loading.value = true;
      const { data } = await api.foods.deleteOne(id);
      if (data && foodStore?.value) {
        this.refreshAll();
      }
    },
    resetWorking() {
      workingFoodData.id = "";
      workingFoodData.name = "";
      workingFoodData.description = "";
      workingFoodData.labelId = undefined;
    },
    setWorking(item: IngredientFood) {
      workingFoodData.id = item.id;
      workingFoodData.name = item.name;
      workingFoodData.description = item.description || "";
      workingFoodData.labelId = item.labelId;
    },
    flushStore() {
      foodStore = null;
    },
  };

  if (!foodStore) {
    foodStore = actions.getAll();
  }

  return { foods: foodStore, workingFoodData, deleteTargetId, actions, validForm };
};
