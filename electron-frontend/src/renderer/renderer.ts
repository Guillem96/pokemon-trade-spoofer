import './index.css';
import $ from 'jquery';
import { POKEMON_NAMES } from '../common/constants';
import { Party, Pokemon } from '../common/models';

const GIF_POKEBALL = '/assets/img/pokeball.gif';
const PNG_POKEBALL = '/assets/img/pokeball.png';

const AVAILABLE_POKEBALL_HTML = `
  <div class="pkm-container nes-container is-rounded">
    <div class="empty nes-pointer">
      <img class="pokeball" src="/assets/img/pokeball.png">
      <h2>Select Pokemon ...</h2>
    </div>
  </div>
`;

const GRAYED_OUT_POKEBALL_HTML = `
  <div class="pkm-container nes-container is-rounded">
    <div class="not-available">
      <img class="pokeball-gray" src="/assets/img/pokeball.png">
    </div>
  </div>
`;

// State
let nPartyPkm = 0;

const renderInitialState = () => {
  $('.content').html(AVAILABLE_POKEBALL_HTML);
  for (let _ = 0; _ < 5; _++) {
    $('.content').append(GRAYED_OUT_POKEBALL_HTML);
  }
};

const animatePokeball = () => {
  $('.pkm-container .empty').on('mouseenter', (e) => {
    $(e.currentTarget).find('img').attr('src', GIF_POKEBALL);
  }).on('mouseleave', (e) => {
    $(e.currentTarget).find('img').attr('src', PNG_POKEBALL);
  });
};

const setSelectPokemonListener = () => {
  $('.pkm-container .empty').on('click', () => {
    $('#select-pkm-dialog').get(0).showModal();
  });
};

const clearSelectedPokemon = () => {
  $('#pokemon-selector').find('option').prop('selected', false);
  $('#pokemon-selector').find('option').first().prop('selected', true);
};

const addNewPokemon = async (dexId: number) => {
  const pkm = await (await fetch(`https://pokeapi.co/api/v2/pokemon/${dexId}`)).json();

  $('.pkm-container').eq(nPartyPkm).html(`
    <div class="name">
      <h2>${pkm.name.toUpperCase()}</h2>
      <h3 id="pkm-id-${nPartyPkm}">#${dexId}</h3>
    </div>
    <img class="sprite" src="${pkm.sprites.versions['generation-ii'].gold.front_transparent}">
    <div class="data">
      <div class="nes-field">
        <label for="nickname-field-${nPartyPkm}">Nickname</label>
        <input type="text" id="nickname-field-${nPartyPkm}" class="nes-input" placeholder="${pkm.name.toUpperCase()}" maxlength="10">
      </div>
    </div>
  `);

  nPartyPkm += 1;
  if (nPartyPkm < 6) {
    $('.pkm-container').eq(nPartyPkm).html(`
      <div class="empty nes-pointer">
        <img class="pokeball" src="/assets/img/pokeball.png">
        <h2>Select Pokemon ...</h2>
      </div>
    `);
    animatePokeball();
    setSelectPokemonListener();
  }
};

const collectPokemonParty = (): Party | null => {
  const trainerName = $('#trainer-name').val();

  if (trainerName === undefined || trainerName === null || trainerName === '') {
    return null;
  }

  const pkmn = $('.pkm-container')
    .map((index: number, el): Pokemon => {
      const dexId = parseInt($(el).find(`#pkm-id-${index}`).text()?.slice(1));
      let nickname = $(el).find(`#nickname-field-${index}`).val()?.toString();
      if (nickname === '' || nickname === undefined || nickname === null) {
        nickname = $(el).find(`#nickname-field-${index}`).attr('placeholder')?.toString();
      }
      return { dexId, nickname };
    })
    .filter((_, o) => !isNaN(o.dexId))
    .toArray();

  return { trainerName: trainerName.toString(), pokemon: pkmn };
};


const startBGBBackend = () => {
  $('#start-backend').attr('disabled', 'true');
  const party = collectPokemonParty();
  if (party !== null) {
    console.log('Starting BGB Backend with the following Pokemon party:');
    console.log(party);
    window.api.startBGBServer(party);
  }
};

$(() => {
  renderInitialState();

  // Animate empty pokemon slot on hover
  animatePokeball();

  // Open select pokemon dialog
  setSelectPokemonListener();

  // Collect party and start backend
  $('#start-backend').on('click', (e) => {
    e.preventDefault();
    startBGBBackend();
  });

  // Clear all team button
  $('#clear-pkmn').on('click', () => {
    nPartyPkm = 0;
    renderInitialState();
  });

  // Pokemon selector dialog
  // 1. Add options to dropdown
  $('#pokemon-selector').html(
    '<option value="" disabled selected hidden>Pokemon ID...</option>' +
    [...Array(251).keys()].map(o => `<option value="${o + 1}">${o + 1} - ${POKEMON_NAMES[o]}</option>`)
      .join(''));

  // 2. On confirm click
  $('#confirm-selection').on('click', (e) => {
    // TODO: Update Pokemon slot
    const selectedPkm = $('#pokemon-selector option:selected').text();
    console.log('Selected pokemon:', $('#pokemon-selector option:selected').text());
    if (selectedPkm !== 'Pokemon ID...') {
      $('#select-pkm-dialog').get(0).close();
      addNewPokemon(Number.parseInt(selectedPkm));
      clearSelectedPokemon();
      e.preventDefault();
    }
  });

  // 3. On cancel click
  $('#cancel-selection').on('click', (e) => {
    $('#select-pkm-dialog').get(0).close();
    clearSelectedPokemon();
    e.preventDefault();
  });
});
