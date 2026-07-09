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

  profile() {
    return apiClient.post('/profile').then((response) => response.data);
  },

  recommend() {
    return apiClient.post('/recommend').then((response) => response.data);
  },

  skillgap() {
    return apiClient.post('/skillgap').then((response) => response.data);
  },

  roadmap() {
    return apiClient.post('/roadmap').then((response) => response.data);
  },
};

export const pipelineSteps = [
  { key: 'validation', resultKey: 'validation', run: ({ transcript, results }) => pipelineApi.validate(transcript, results?.validation?.partial_profile) },
  { key: 'profile', resultKey: 'profileAnalysis', run: () => pipelineApi.profile() },
  { key: 'career', resultKey: 'recommendations', run: () => pipelineApi.recommend() },
  { key: 'skillgap', resultKey: 'skillGap', run: () => pipelineApi.skillgap() },
  { key: 'roadmap', resultKey: 'roadmap', run: () => pipelineApi.roadmap() },
];
