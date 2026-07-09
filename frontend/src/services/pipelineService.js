import apiClient from './apiClient';

// ---------------------------------------------------------------------------
// Debug helper — logs an object as a table with key/value/type columns
// ---------------------------------------------------------------------------
function _debugTable(label, obj) {
  if (!obj || typeof obj !== 'object') {
    console.log(label, obj);
    return;
  }
  try {
    if (Array.isArray(obj)) {
      console.log(label, `[Array length=${obj.length}]`);
      console.table(obj.slice(0, 5)); // show first 5 items
    } else {
      console.log(label);
      console.table(
        Object.entries(obj).map(([k, v]) => ({
          key: k,
          type: Array.isArray(v) ? `Array(${v.length})` : typeof v,
          preview: Array.isArray(v) ? v.slice(0, 3).join(', ') : String(v).slice(0, 80),
        })),
      );
    }
  } catch (_) {
    console.log(label, obj);
  }
}

export const pipelineApi = {
  // -----------------------------------------------------------------------
  // VALIDATE
  // -----------------------------------------------------------------------
  validate(transcript, partialProfile) {
    console.group('%c🔍 VALIDATE — service call started', 'color: #9c27b0; font-weight: bold; font-size:13px;');
    console.log('Endpoint: POST /validate');
    console.log('transcript (first 200 chars):', String(transcript || '').slice(0, 200));
    console.log('partialProfile:', partialProfile ?? 'none');
    if (partialProfile) _debugTable('Partial Profile Table:', partialProfile);
    console.groupEnd();

    return apiClient
      .post('/validate', {
        transcript,
        ...(partialProfile ? { partial_profile: partialProfile } : {}),
      })
      .then((response) => {
        console.group('%c✅ VALIDATE — service call resolved', 'color: #4CAF50; font-weight: bold; font-size:13px;');
        console.log('status:', response.data?.status);
        console.log('missing_fields:', response.data?.missing_fields ?? 'none');
        _debugTable('Profile (if complete):', response.data?.profile);
        console.groupEnd();
        return response.data;
      })
      .catch((err) => {
        console.group('%c❌ VALIDATE — service call FAILED', 'color: #F44336; font-weight: bold; font-size:13px;');
        console.error('Error:', err);
        console.groupEnd();
        throw err;
      });
  },

  // -----------------------------------------------------------------------
  // PROFILE
  // -----------------------------------------------------------------------
  profile(studentProfile) {
    console.group('%c🔍 PROFILE — service call started', 'color: #9c27b0; font-weight: bold; font-size:13px;');
    console.log('Endpoint: POST /profile');
    _debugTable('student_profile:', studentProfile);
    console.groupEnd();

    return apiClient
      .post('/profile', { student_profile: studentProfile })
      .then((response) => {
        console.group('%c✅ PROFILE — service call resolved', 'color: #4CAF50; font-weight: bold; font-size:13px;');
        console.log('career_readiness_score:', response.data?.career_readiness_score);
        console.log('profile_tier:', response.data?.profile_tier);
        console.log('score_band:', response.data?.score_band);
        _debugTable('Profile Analysis:', response.data);
        console.groupEnd();
        return response.data;
      })
      .catch((err) => {
        console.group('%c❌ PROFILE — service call FAILED', 'color: #F44336; font-weight: bold; font-size:13px;');
        console.error('Error:', err);
        console.groupEnd();
        throw err;
      });
  },

  // -----------------------------------------------------------------------
  // CAREER (recommend)
  // -----------------------------------------------------------------------
  recommend(studentProfile, profileAnalysis) {
    console.group('%c🔍 CAREER — service call started', 'color: #9c27b0; font-weight: bold; font-size:13px;');
    console.log('Endpoint: POST /recommend');
    _debugTable('student_profile:', studentProfile);
    _debugTable('profile_analysis:', profileAnalysis);
    console.groupEnd();

    return apiClient
      .post('/recommend', { student_profile: studentProfile, profile_analysis: profileAnalysis })
      .then((response) => {
        console.group('%c✅ CAREER — service call resolved', 'color: #4CAF50; font-weight: bold; font-size:13px;');
        const recs = Array.isArray(response.data) ? response.data : [];
        console.log('Number of recommendations:', recs.length);
        if (recs.length > 0) {
          console.table(recs.map((r) => ({ title: r.title, confidence: r.confidence_percent, career_id: r.career_id })));
        }
        console.groupEnd();
        return response.data;
      })
      .catch((err) => {
        console.group('%c❌ CAREER — service call FAILED', 'color: #F44336; font-weight: bold; font-size:13px;');
        console.error('Error:', err);
        console.groupEnd();
        throw err;
      });
  },

  // -----------------------------------------------------------------------
  // SKILL GAP
  // -----------------------------------------------------------------------
  skillgap(studentProfile, recommendations) {
    console.group('%c🔍 SKILL GAP — service call started', 'color: #9c27b0; font-weight: bold; font-size:13px;');
    console.log('Endpoint: POST /skillgap');
    _debugTable('student_profile:', studentProfile);
    console.log('recommendations count:', Array.isArray(recommendations) ? recommendations.length : 'N/A');
    console.log('top recommendation:', recommendations?.[0]?.title ?? 'none');
    console.groupEnd();

    return apiClient
      .post('/skillgap', { student_profile: studentProfile, recommendations })
      .then((response) => {
        console.group('%c✅ SKILL GAP — service call resolved', 'color: #4CAF50; font-weight: bold; font-size:13px;');
        const sg = response.data;
        console.log('target_career:', sg?.target_career);
        console.log('skills_already_have:', sg?.skills_already_have);
        console.log('skills_to_learn count:', sg?.skills_to_learn?.length);
        console.log('tools_to_learn count:', sg?.tools_to_learn?.length);
        _debugTable('gap_summary:', sg?.gap_summary);
        console.groupEnd();
        return response.data;
      })
      .catch((err) => {
        console.group('%c❌ SKILL GAP — service call FAILED', 'color: #F44336; font-weight: bold; font-size:13px;');
        console.error('Error:', err);
        console.groupEnd();
        throw err;
      });
  },

  // -----------------------------------------------------------------------
  // ROADMAP
  // -----------------------------------------------------------------------
  roadmap(studentProfile, profileAnalysis, skillGap, recommendations) {
    console.group('%c🔍 ROADMAP — service call started', 'color: #9c27b0; font-weight: bold; font-size:13px;');
    console.log('Endpoint: POST /roadmap');
    _debugTable('student_profile:', studentProfile);
    _debugTable('profile_analysis:', profileAnalysis);
    console.log('skill_gap (keys):', skillGap ? Object.keys(skillGap) : 'null/undefined ⚠️');
    console.log('recommendations count:', Array.isArray(recommendations) ? recommendations.length : 'N/A ⚠️');
    if (!skillGap) console.warn('⚠️ skill_gap is null/undefined — roadmap will likely fail or be empty');
    if (!recommendations?.length) console.warn('⚠️ recommendations is empty — roadmap will likely fail or be empty');
    console.groupEnd();

    return apiClient
      .post('/roadmap', {
        student_profile: studentProfile,
        profile_analysis: profileAnalysis,
        skill_gap: skillGap,
        recommendations,
      })
      .then((response) => {
        console.group('%c✅ ROADMAP — service call resolved', 'color: #4CAF50; font-weight: bold; font-size:13px;');
        const rm = response.data;
        console.log('target_career:', rm?.target_career);
        console.log('profile_tier:', rm?.profile_tier);
        console.log('30_day keys:', rm?.['30_day'] ? Object.keys(rm['30_day']) : 'MISSING ⚠️');
        console.log('60_day keys:', rm?.['60_day'] ? Object.keys(rm['60_day']) : 'MISSING ⚠️');
        console.log('90_day keys:', rm?.['90_day'] ? Object.keys(rm['90_day']) : 'MISSING ⚠️');
        console.log('30_day focus:', rm?.['30_day']?.focus ?? '⚠️ empty');
        console.log('60_day focus:', rm?.['60_day']?.focus ?? '⚠️ empty');
        console.log('90_day focus:', rm?.['90_day']?.focus ?? '⚠️ empty');
        console.log('(full roadmap object):', rm);
        console.groupEnd();
        return response.data;
      })
      .catch((err) => {
        console.group('%c❌ ROADMAP — service call FAILED', 'color: #F44336; font-weight: bold; font-size:13px;');
        console.error('Error:', err);
        console.groupEnd();
        throw err;
      });
  },
};

export const pipelineSteps = [
  {
    key: 'validation',
    resultKey: 'validation',
    run: ({ transcript, results }) =>
      pipelineApi.validate(transcript, results?.validation?.partial_profile),
  },
  {
    key: 'profile',
    resultKey: 'profileAnalysis',
    run: ({ results }) =>
      pipelineApi.profile(results.validation.profile),
  },
  {
    key: 'career',
    resultKey: 'recommendations',
    run: ({ results }) =>
      pipelineApi.recommend(results.validation.profile, results.profileAnalysis),
  },
  {
    key: 'skillgap',
    resultKey: 'skillGap',
    run: ({ results }) =>
      pipelineApi.skillgap(results.validation.profile, results.recommendations),
  },
  {
    key: 'roadmap',
    resultKey: 'roadmap',
    run: ({ results }) =>
      pipelineApi.roadmap(
        results.validation.profile,
        results.profileAnalysis,
        results.skillGap,
        results.recommendations,
      ),
  },
];
