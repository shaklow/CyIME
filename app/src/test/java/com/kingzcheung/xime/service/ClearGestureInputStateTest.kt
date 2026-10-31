package com.kingzcheung.xime.service

import org.junit.Assert.*
import org.junit.Test

/** 清空和撤回共用的输入态判定；候选栏有内容不等于仍在组词。 */
class ClearGestureInputStateTest {
    private fun blocksDocumentClear(state: CandidateState): Boolean =
        state.hasUncommittedInputForClear(false)

    @Test fun committedTextCanBeClearedInOneGestureWithAssociationCandidates() {
        assertFalse(blocksDocumentClear(CandidateState(associationCandidates = listOf("世界", "朋友"))))
    }

    @Test fun clipboardSuggestionsDoNotRequireAnExtraClearGesture() {
        assertFalse(blocksDocumentClear(CandidateState(
            candidates = listOf("复制的文字"), isShowingRecentClipboard = true,
        )))
    }

    @Test fun idleInputDoesNotBlockClearOrUndo() {
        assertFalse(blocksDocumentClear(CandidateState()))
    }

    @Test fun unfinishedChineseInputStillProtectsTheCommittedDocument() {
        for (state in listOf(
            CandidateState(isComposing = true, candidates = listOf("你好")),
            CandidateState(inputText = "nihao"),
            CandidateState(preeditText = "ni'hao"),
        )) assertTrue(blocksDocumentClear(state))
    }

    @Test fun englishCompletionStillClearsTheCurrentWordOnly() {
        assertTrue(blocksDocumentClear(CandidateState(
            pendingEnglishText = "hell", associationCandidates = listOf("hello"),
        )))
    }

    @Test fun partiallySelectedT9InputStillProtectsTheCommittedDocument() {
        assertTrue(CandidateState().hasUncommittedInputForClear(true))
    }
}
