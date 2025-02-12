<template>
  <section @keyup.ctrl.90="undoMerge">
    <!-- Ingredient Link Editor -->
    <v-dialog v-model="dialog" width="600">
      <v-card :ripple="false">
        <v-app-bar dark color="primary" class="mt-n1 mb-3">
          <v-icon large left>
            {{ $globals.icons.link }}
          </v-icon>
          <v-toolbar-title class="headline"> Ingredient Linker </v-toolbar-title>
          <v-spacer></v-spacer>
        </v-app-bar>

        <v-card-text class="pt-4">
          <p>
            {{ activeText }}
          </p>
          <v-divider class="mb-4"></v-divider>
          <v-checkbox
            v-for="ing in unusedIngredients"
            :key="ing.referenceId"
            v-model="activeRefs"
            :value="ing.referenceId"
            class="mb-n2 mt-n2"
          >
            <template #label>
              <div v-html="parseIngredientText(ing, disableAmount)"></div>
            </template>
          </v-checkbox>

          <template v-if="usedIngredients.length > 0">
            <h4 class="py-3 ml-1">Linked to other step</h4>
            <v-checkbox
              v-for="ing in usedIngredients"
              :key="ing.referenceId"
              v-model="activeRefs"
              :value="ing.referenceId"
              class="mb-n2 mt-n2"
            >
              <template #label>
                <div v-html="parseIngredientText(ing, disableAmount)"></div>
              </template>
            </v-checkbox>
          </template>
        </v-card-text>

        <v-divider></v-divider>

        <v-card-actions>
          <BaseButton cancel @click="dialog = false"> </BaseButton>
          <v-spacer></v-spacer>
          <BaseButton color="info" @click="autoSetReferences">
            <template #icon> {{ $globals.icons.robot }}</template>
            Auto
          </BaseButton>
          <BaseButton save @click="setIngredientIds"> </BaseButton>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <div class="d-flex justify-space-between justify-start">
      <h2 class="mb-4 mt-1">{{ $t("recipe.instructions") }}</h2>
      <BaseButton v-if="!public" minor :to="$router.currentRoute.path + '/cook'" cancel color="primary">
        <template #icon>
          {{ $globals.icons.primary }}
        </template>
        Cook
      </BaseButton>
    </div>
    <draggable
      :disabled="!edit"
      :value="value"
      handle=".handle"
      v-bind="{
        animation: 200,
        group: 'description',
        ghostClass: 'ghost',
      }"
      @input="updateIndex"
      @start="drag = true"
      @end="drag = false"
    >
      <TransitionGroup type="transition" :name="!drag ? 'flip-list' : ''">
        <div v-for="(step, index) in value" :key="step.id" class="list-group-item">
          <v-app-bar
            v-if="showTitleEditor[step.id]"
            class="primary mx-1 mt-6"
            style="cursor: pointer"
            dark
            dense
            rounded
            @click="toggleCollapseSection(index)"
          >
            <v-toolbar-title v-if="!edit" class="headline">
              <v-app-bar-title> {{ step.title }} </v-app-bar-title>
            </v-toolbar-title>
            <v-text-field
              v-if="edit"
              v-model="step.title"
              class="headline pa-0 mt-5"
              dense
              solo
              flat
              :placeholder="$t('recipe.section-title')"
              background-color="primary"
            >
            </v-text-field>
          </v-app-bar>
          <v-hover v-slot="{ hover }">
            <v-card
              class="ma-1"
              :class="[{ 'on-hover': hover }, isChecked(index)]"
              :elevation="hover ? 12 : 2"
              :ripple="false"
              @click="toggleDisabled(index)"
            >
              <v-card-title :class="{ 'pb-0': !isChecked(index) }">
                <span class="handle">
                  <v-icon v-if="edit" size="26" class="pb-1">{{ $globals.icons.arrowUpDown }}</v-icon>
                  {{ $t("recipe.step-index", { step: index + 1 }) }}
                </span>
                <template v-if="edit">
                  <div class="ml-auto">
                    <BaseButtonGroup
                      :large="false"
                      :buttons="[
                        {
                          icon: $globals.icons.delete,
                          text: $tc('general.delete'),
                          event: 'delete',
                        },
                        {
                          icon: $globals.icons.dotsVertical,
                          text: '',
                          event: 'open',
                          children: [
                            {
                              text: 'Toggle Section',
                              event: 'toggle-section',
                            },
                            {
                              text: 'Link Ingredients',
                              event: 'link-ingredients',
                            },
                            {
                              text: 'Merge Above',
                              event: 'merge-above',
                            },
                            {
                              icon: previewStates[index] ? $globals.icons.edit : $globals.icons.eye,
                              text: previewStates[index] ? 'Edit Markdown' : 'Preview Markdown',
                              event: 'preview-step',
                            },
                          ],
                        },
                      ]"
                      @merge-above="mergeAbove(index - 1, index)"
                      @toggle-section="toggleShowTitle(step.id)"
                      @link-ingredients="openDialog(index, step.ingredientReferences, step.text)"
                      @preview-step="togglePreviewState(index)"
                      @delete="value.splice(index, 1)"
                    />
                  </div>
                </template>
                <v-fade-transition>
                  <v-icon v-show="isChecked(index)" size="24" class="ml-auto" color="success">
                    {{ $globals.icons.checkboxMarkedCircle }}
                  </v-icon>
                </v-fade-transition>
              </v-card-title>
              <v-card-text v-if="edit">
                <MarkdownEditor
                  v-model="value[index]['text']"
                  :preview.sync="previewStates[index]"
                  :display-preview="false"
                />
                <div
                  v-for="ing in step.ingredientReferences"
                  :key="ing.referenceId"
                  v-html="getIngredientByRefId(ing.referenceId)"
                />
              </v-card-text>
              <v-expand-transition>
                <div v-show="!isChecked(index) && !edit" class="m-0 p-0">
                  <v-card-text class="markdown">
                    <VueMarkdown class="markdown" :source="step.text"> </VueMarkdown>
                  </v-card-text>
                </div>
              </v-expand-transition>
            </v-card>
          </v-hover>
        </div>
      </TransitionGroup>
    </draggable>
  </section>
</template>

<script lang="ts">
import draggable from "vuedraggable";
// @ts-ignore vue-markdown has no types
import VueMarkdown from "@adapttive/vue-markdown";
import { ref, toRefs, reactive, defineComponent, watch, onMounted } from "@nuxtjs/composition-api";
import { RecipeStep, IngredientReferences, RecipeIngredient } from "~/types/api-types/recipe";
import { parseIngredientText } from "~/composables/recipes";
import { uuid4 } from "~/composables/use-utils";

interface MergerHistory {
  target: number;
  source: number;
  targetText: string;
  sourceText: string;
}

export default defineComponent({
  components: {
    VueMarkdown,
    draggable,
  },
  props: {
    value: {
      type: Array as () => RecipeStep[],
      required: true,
    },
    edit: {
      type: Boolean,
      default: true,
    },
    ingredients: {
      type: Array as () => RecipeIngredient[],
      default: () => [],
    },
    disableAmount: {
      type: Boolean,
      default: false,
    },
    public: {
      type: Boolean,
      default: false,
    },
  },

  setup(props, context) {
    const state = reactive({
      dialog: false,
      disabledSteps: [] as number[],
      unusedIngredients: [] as RecipeIngredient[],
      usedIngredients: [] as RecipeIngredient[],
    });

    const showTitleEditor = ref<{ [key: string]: boolean }>({});

    const actionEvents = [
      {
        text: "Toggle Section",
        event: "toggle-section",
      },
      {
        text: "Link Ingredients",
        event: "link-ingredients",
      },
      {
        text: "Merge Above",
        event: "merge-above",
      },
    ];

    // ===============================================================
    // UI State Helpers

    function validateTitle(title: string | undefined) {
      return !(title === null || title === "" || title === undefined);
    }

    watch(props.value, (v) => {
      state.disabledSteps = [];

      v.forEach((element: RecipeStep) => {
        if (element.id !== undefined) {
          showTitleEditor.value[element.id] = validateTitle(element.title);
        }
      });
    });

    // Eliminate state with an eager call to watcher?
    onMounted(() => {
      props.value.forEach((element) => {
        if (element.id !== undefined) {
          showTitleEditor.value[element.id] = validateTitle(element.title);
        }

        showTitleEditor.value = { ...showTitleEditor.value };
      });
    });

    function toggleDisabled(stepIndex: number) {
      if (props.edit) {
        return;
      }
      if (state.disabledSteps.includes(stepIndex)) {
        const index = state.disabledSteps.indexOf(stepIndex);
        if (index !== -1) {
          state.disabledSteps.splice(index, 1);
        }
      } else {
        state.disabledSteps.push(stepIndex);
      }
    }

    function isChecked(stepIndex: number) {
      if (state.disabledSteps.includes(stepIndex) && !props.edit) {
        return "disabled-card";
      }
    }

    function toggleShowTitle(id: string) {
      showTitleEditor.value[id] = !showTitleEditor.value[id];

      const temp = { ...showTitleEditor.value };
      showTitleEditor.value = temp;
    }

    function updateIndex(data: RecipeStep) {
      context.emit("input", data);
    }

    // ===============================================================
    // Ingredient Linker
    const activeRefs = ref<string[]>([]);
    const activeIndex = ref(0);
    const activeText = ref("");

    function openDialog(idx: number, refs: IngredientReferences[], text: string) {
      setUsedIngredients();
      activeText.value = text;
      activeIndex.value = idx;
      state.dialog = true;
      activeRefs.value = refs.map((ref) => ref.referenceId ?? "");
    }

    function setIngredientIds() {
      const instruction = props.value[activeIndex.value];
      instruction.ingredientReferences = activeRefs.value.map((ref) => {
        return {
          referenceId: ref,
        };
      });
      state.dialog = false;
    }

    function setUsedIngredients() {
      const usedRefs: { [key: string]: boolean } = {};

      props.value.forEach((element) => {
        element.ingredientReferences?.forEach((ref) => {
          if (ref.referenceId !== undefined) {
            usedRefs[ref.referenceId] = true;
          }
        });
      });

      state.usedIngredients = props.ingredients.filter((ing) => {
        return ing.referenceId !== undefined && ing.referenceId in usedRefs;
      });

      state.unusedIngredients = props.ingredients.filter((ing) => {
        return !(ing.referenceId !== undefined && ing.referenceId in usedRefs);
      });
    }

    function autoSetReferences() {
      // Ingore matching blacklisted words when auto-linking - This is kind of a cludgey implementation. We're blacklisting common words but
      // other common phrases trigger false positives and I'm not sure how else to approach this. In the future I maybe look at looking directly
      // at the food variable and seeing if the food is in the instructions, but I still need to support those who don't want to provide the value
      // and only use the "notes" feature.
      const blackListedText = [
        "and",
        "or",
        "the",
        "a",
        "an",
        "of",
        "in",
        "on",
        "to",
        "for",
        "by",
        "with",
        "without",
        "",
        " ",
      ];
      const blackListedRegexMatch = /\d/gm; // Match Any Number

      // Check if any of the words in the active text match the ingredient text
      const instructionsByWord = activeText.value.toLowerCase().split(" ");

      instructionsByWord.forEach((word) => {
        if (blackListedText.includes(word) || word.match(blackListedRegexMatch)) {
          return;
        }

        props.ingredients.forEach((ingredient) => {
          const searchText = parseIngredientText(ingredient, props.disableAmount);

          if (ingredient.referenceId === undefined) {
            return;
          }

          if (searchText.toLowerCase().includes(" " + word) && !activeRefs.value.includes(ingredient.referenceId)) {
            console.info("Word Matched", `'${word}'`, ingredient.note);
            activeRefs.value.push(ingredient.referenceId);
          }
        });
      });
    }

    function getIngredientByRefId(refId: string) {
      const ing = props.ingredients.find((ing) => ing.referenceId === refId) || "";
      if (ing === "") {
        return "";
      }
      return parseIngredientText(ing, props.disableAmount);
    }

    // ===============================================================
    // Instruction Merger
    const mergeHistory = ref<MergerHistory[]>([]);

    function mergeAbove(target: number, source: number) {
      if (target < 0) {
        return;
      }

      mergeHistory.value.push({
        target,
        source,
        targetText: props.value[target].text,
        sourceText: props.value[source].text,
      });

      props.value[target].text += " " + props.value[source].text;
      props.value.splice(source, 1);
    }

    function undoMerge(event: KeyboardEvent) {
      if (event.ctrlKey && event.code === "KeyZ") {
        if (!(mergeHistory.value?.length > 0)) {
          return;
        }

        const lastMerge = mergeHistory.value.pop();
        if (!lastMerge) {
          return;
        }

        props.value[lastMerge.target].text = lastMerge.targetText;
        props.value.splice(lastMerge.source, 0, {
          id: uuid4(),
          title: "",
          text: lastMerge.sourceText,
          ingredientReferences: [],
        });
      }
    }

    const previewStates = ref<boolean[]>([]);

    function togglePreviewState(index: number) {
      const temp = [...previewStates.value];
      temp[index] = !temp[index];
      previewStates.value = temp;
    }

    function toggleCollapseSection(index: number) {
      const sectionSteps: number[] = [];

      for (let i = index; i < props.value.length; i++) {
        if (!(i === index) && validateTitle(props.value[i].title)) {
          break;
        } else {
          sectionSteps.push(i);
        }
      }

      const allCollapsed = sectionSteps.every((idx) => state.disabledSteps.includes(idx));

      if (allCollapsed) {
        state.disabledSteps = state.disabledSteps.filter((idx) => !sectionSteps.includes(idx));
      } else {
        state.disabledSteps = [...state.disabledSteps, ...sectionSteps];
      }
    }

    const drag = ref(false);

    return {
      drag,
      togglePreviewState,
      toggleCollapseSection,
      previewStates,
      ...toRefs(state),
      actionEvents,
      activeRefs,
      activeText,
      getIngredientByRefId,
      showTitleEditor,
      mergeAbove,
      openDialog,
      setIngredientIds,
      undoMerge,
      toggleDisabled,
      isChecked,
      toggleShowTitle,
      updateIndex,
      autoSetReferences,
      parseIngredientText,
    };
  },
});
</script>

<style lang="css" scoped>
.v-card--link:before {
  background: none;
}

/** Select all li under .markdown class */
.markdown >>> ul > li {
  display: list-item;
  list-style-type: disc !important;
}

/** Select all li under .markdown class */
.markdown >>> ol > li {
  display: list-item;
}

.flip-list-move {
  transition: transform 0.5s;
}
.no-move {
  transition: transform 0s;
}
.ghost {
  opacity: 0.5;
}
.list-group {
  min-height: 38px;
}
.list-group-item {
  cursor: move;
}
.list-group-item i {
  cursor: pointer;
}
</style>
