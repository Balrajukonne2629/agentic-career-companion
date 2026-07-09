import apiClient from './apiClient';

export const pipelineApi = {
  validate(transcript, partialProfile) {
    return apiClient
      .post('/validate', {
        transcript,
        ...(partialProfile ? { partial_profile: partialProfile } : {}),
      })
      .then((response) => response.data);
  },

  profile(studentProfile) {
    return apiClient
      .post('/profile', { student_profile: studentProfile })
      .then((response) => response.data);
  },

  recommend(studentProfile, profileAnalysis) {
    return apiClient
      .post('/recommend', { student_profile: studentProfile, profile_analysis: profileAnalysis })
      .then((response) => response.data);
  },

  skillgap(studentProfile, recommendations) {
    return apiClient
      .post('/skillgap', { student_profile: studentProfile, recommendations })
      .then((response) => response.data);
  },

  roadmap(studentProfile, profileAnalysis, skillGap, recommendations) {
    return apiClient
      .post('/roadmap', {
        student_profile: studentProfile,
        profile_analysis: profileAnalysis,
        skill_gap: skillGap,
        recommendations,
      })
      .then((response) => response.data);
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
